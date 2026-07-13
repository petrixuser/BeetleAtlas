"""Pydantic-Schemas fuer die Schreib-Endpunkte der Kaefer-API.

Enthaelt die Eingabe-Validierung (Create/Update) und das Antwort-Schema.
Gemeinsame Regeln von Create und Update:
  * Textfelder werden getrimmt, leere Strings werden zu None.
  * ``basis_of_record`` muss ein gueltiger GBIF-Wert sein.
  * ``country`` muss ein lateinamerikanisches Land sein.
  * ``event_date`` muss JJJJ, JJJJ-MM oder JJJJ-MM-TT sein.
  * Breiten-/Laengengrad nur gemeinsam und innerhalb der LATAM-Grenzen.
Die beiden Request-Klassen wiederholen diese Validatoren bewusst, damit die
Feld-Defaults (Create: Pflichtfelder, Update: alles optional) getrennt bleiben.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.config.beetle_validation import (
    GBIF_BASIS_OF_RECORD,
    LATAM_MAX_LAT,
    LATAM_MAX_LON,
    LATAM_MIN_LAT,
    LATAM_MIN_LON,
    coordinates_in_latam_bounds,
    country_in_latam,
)


BeetleRecordStatus = Literal["active", "deleted"]


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    """Trimmt Text; ein leerer String wird zu None (einheitliche Speicherung)."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class BeetleMediaItem(BaseModel):
    """Ein Bild eines manuellen Kaefers (Mehrbild-Feature, 1:N)."""

    image_url: str = Field(min_length=1, max_length=2048)
    media_references: Optional[str] = Field(default=None, max_length=2048)
    media_creator: Optional[str] = Field(default=None, max_length=512)
    media_publisher: Optional[str] = Field(default=None, max_length=512)
    media_rights_holder: Optional[str] = Field(default=None, max_length=512)
    media_license: Optional[str] = Field(default=None, max_length=512)


class _BeetleWriteValidatorsMixin(BaseModel):
    """Gemeinsame Feld- und Modell-Validatoren fuer Create- und Update-Request.

    ``check_fields=False``, weil die referenzierten Felder erst in den
    Unterklassen (Create/Update) definiert werden.
    """

    @field_validator(
        "taxon_id",
        "scientific_name",
        "scientific_name_authorship",
        "family",
        "genus",
        "specific_epithet",
        "recorded_by",
        "catalogue_number",
        "identification_id",
        "identified_by",
        "event_date",
        "verbatim_event_date",
        "basis_of_record",
        "dataset_name",
        "institution_code",
        "image_url",
        "media_references",
        "media_creator",
        "media_publisher",
        "media_rights_holder",
        "media_license",
        "coordinate_uncertainty",
        "country",
        "region",
        "city",
        "verbatim_locality",
        "location",
        "notes",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def normalize_text_fields(cls, value):
        """Trimmt Textfelder; leere Strings werden zu None."""
        if isinstance(value, str):
            return _normalize_optional_text(value)
        return value

    @field_validator("basis_of_record", check_fields=False)
    @classmethod
    def validate_basis_of_record(cls, value: Optional[str]) -> Optional[str]:
        """Erzwingt einen gueltigen GBIF-basis_of_record-Wert (Grossschreibung)."""
        if value is None:
            return None
        normalized = value.upper()
        if normalized not in GBIF_BASIS_OF_RECORD:
            allowed = ", ".join(sorted(GBIF_BASIS_OF_RECORD))
            raise ValueError(f"basis_of_record muss einer der folgenden Werte sein: {allowed}")
        return normalized

    @field_validator("country", check_fields=False)
    @classmethod
    def validate_country(cls, value: Optional[str]) -> Optional[str]:
        """Erzwingt ein lateinamerikanisches Land (Code oder Name)."""
        if value is None:
            return None
        if not country_in_latam(value):
            raise ValueError("country muss ein lateinamerikanischer Laendercode oder -name sein")
        return value

    @field_validator("event_date", check_fields=False)
    @classmethod
    def validate_event_date(cls, value: Optional[str]) -> Optional[str]:
        """Prueft das Datumsformat (JJJJ, JJJJ-MM oder JJJJ-MM-TT)."""
        if value is None:
            return None
        if len(value) not in (4, 7, 10):
            raise ValueError("event_date muss JJJJ, JJJJ-MM oder JJJJ-MM-TT sein")
        if len(value) == 4 and not value.isdigit():
            raise ValueError("event_date muss JJJJ, JJJJ-MM oder JJJJ-MM-TT sein")
        if len(value) == 7 and not (value[0:4].isdigit() and value[4] == "-" and value[5:7].isdigit()):
            raise ValueError("event_date muss JJJJ, JJJJ-MM oder JJJJ-MM-TT sein")
        if len(value) == 10 and not (
            value[0:4].isdigit() and value[4] == "-" and value[5:7].isdigit() and value[7] == "-" and value[8:10].isdigit()
        ):
            raise ValueError("event_date muss JJJJ, JJJJ-MM oder JJJJ-MM-TT sein")
        return value

    @model_validator(mode="after")
    def validate_coordinate_pair(self):
        """Breiten-/Laengengrad nur gemeinsam und innerhalb der LATAM-Grenzen."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude und longitude muessen zusammen angegeben werden")
        if self.latitude is not None and self.longitude is not None:
            if not coordinates_in_latam_bounds(self.latitude, self.longitude):
                raise ValueError(
                    "latitude/longitude muessen innerhalb der Grenzen Lateinamerikas liegen "
                    f"(lat {LATAM_MIN_LAT}..{LATAM_MAX_LAT}, lon {LATAM_MIN_LON}..{LATAM_MAX_LON})"
                )
        return self


class BeetleCreateRequest(_BeetleWriteValidatorsMixin):
    """Eingabe zum Anlegen eines manuellen Kaefers (Pflicht: Name + Familie)."""

    gbif_id: Optional[int] = Field(default=None, ge=1)
    taxon_id: Optional[str] = Field(default=None, max_length=128)
    scientific_name: str = Field(min_length=2, max_length=512)
    media_items: Optional[list[BeetleMediaItem]] = None
    scientific_name_authorship: Optional[str] = Field(default=None, max_length=512)
    family: str = Field(min_length=2, max_length=255)
    genus: Optional[str] = Field(default=None, max_length=255)
    specific_epithet: Optional[str] = Field(default=None, max_length=255)
    recorded_by: Optional[str] = Field(default=None, max_length=512)
    catalogue_number: Optional[str] = Field(default=None, max_length=255)
    identification_id: Optional[str] = Field(default=None, max_length=255)
    identified_by: Optional[str] = Field(default=None, max_length=512)
    event_date: Optional[str] = Field(default=None, max_length=128)
    verbatim_event_date: Optional[str] = Field(default=None, max_length=255)
    basis_of_record: Optional[str] = Field(default=None, max_length=128)
    dataset_name: Optional[str] = Field(default=None, max_length=512)
    institution_code: Optional[str] = Field(default=None, max_length=255)
    image_available: Optional[bool] = None
    image_url: Optional[str] = Field(default=None, max_length=2048)
    media_references: Optional[str] = Field(default=None, max_length=2048)
    media_creator: Optional[str] = Field(default=None, max_length=512)
    media_publisher: Optional[str] = Field(default=None, max_length=512)
    media_rights_holder: Optional[str] = Field(default=None, max_length=512)
    media_license: Optional[str] = Field(default=None, max_length=512)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    coordinate_uncertainty: Optional[str] = Field(default=None, max_length=128)
    country: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=255)
    verbatim_locality: Optional[str] = Field(default=None, max_length=4000)
    location: Optional[str] = Field(default=None, max_length=1024)
    notes: Optional[str] = Field(default=None, max_length=4000)


class BeetleUpdateRequest(_BeetleWriteValidatorsMixin):
    """Eingabe zum Aktualisieren eines Kaefers (alle Felder optional / Patch)."""

    gbif_id: Optional[int] = Field(default=None, ge=1)
    taxon_id: Optional[str] = Field(default=None, max_length=128)
    scientific_name: Optional[str] = Field(default=None, min_length=2, max_length=512)
    media_items: Optional[list[BeetleMediaItem]] = None
    scientific_name_authorship: Optional[str] = Field(default=None, max_length=512)
    family: Optional[str] = Field(default=None, min_length=2, max_length=255)
    genus: Optional[str] = Field(default=None, max_length=255)
    specific_epithet: Optional[str] = Field(default=None, max_length=255)
    recorded_by: Optional[str] = Field(default=None, max_length=512)
    catalogue_number: Optional[str] = Field(default=None, max_length=255)
    identification_id: Optional[str] = Field(default=None, max_length=255)
    identified_by: Optional[str] = Field(default=None, max_length=512)
    event_date: Optional[str] = Field(default=None, max_length=128)
    verbatim_event_date: Optional[str] = Field(default=None, max_length=255)
    basis_of_record: Optional[str] = Field(default=None, max_length=128)
    dataset_name: Optional[str] = Field(default=None, max_length=512)
    institution_code: Optional[str] = Field(default=None, max_length=255)
    image_available: Optional[bool] = None
    image_url: Optional[str] = Field(default=None, max_length=2048)
    media_references: Optional[str] = Field(default=None, max_length=2048)
    media_creator: Optional[str] = Field(default=None, max_length=512)
    media_publisher: Optional[str] = Field(default=None, max_length=512)
    media_rights_holder: Optional[str] = Field(default=None, max_length=512)
    media_license: Optional[str] = Field(default=None, max_length=512)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    coordinate_uncertainty: Optional[str] = Field(default=None, max_length=128)
    country: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=255)
    verbatim_locality: Optional[str] = Field(default=None, max_length=4000)
    location: Optional[str] = Field(default=None, max_length=1024)
    notes: Optional[str] = Field(default=None, max_length=4000)


class BeetleRecordResponse(BaseModel):
    """Antwort-Schema eines Kaefer-Datensatzes (flache Sicht ueber den View)."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    gbif_id: Optional[int] = None
    taxon_id: Optional[str] = None
    scientific_name: str
    scientific_name_authorship: Optional[str] = None
    family: str
    genus: Optional[str] = None
    specific_epithet: Optional[str] = None
    recorded_by: Optional[str] = None
    catalogue_number: Optional[str] = None
    identification_id: Optional[str] = None
    identified_by: Optional[str] = None
    event_date: Optional[str] = None
    verbatim_event_date: Optional[str] = None
    basis_of_record: Optional[str] = None
    dataset_name: Optional[str] = None
    institution_code: Optional[str] = None
    image_available: Optional[bool] = None
    image_url: Optional[str] = None
    media_references: Optional[str] = None
    media_creator: Optional[str] = None
    media_publisher: Optional[str] = None
    media_rights_holder: Optional[str] = None
    media_license: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinate_uncertainty: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    verbatim_locality: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: BeetleRecordStatus
    created_by: int = Field(alias="createdBy")
    updated_by: Optional[int] = Field(default=None, alias="updatedBy")
    deleted_by: Optional[int] = Field(default=None, alias="deletedBy")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    deleted_at: Optional[datetime] = Field(default=None, alias="deletedAt")
