from dataclasses import dataclass
from enum import Enum, IntFlag
from datetime import datetime
from types import UnionType, GenericAlias
from inspect import isclass
from typing import Type
from contextlib import suppress


class Requirement(Enum):
    required = 1
    optional = 2
    unsupported = 3


class Dependency(Enum):
    required = 1
    optional = 2
    incompatible = 3


class Status(Enum):
    approved = 1
    rejected = 2
    draft = 3
    unlisted = 4
    archived = 5
    processing = 6
    unknown = 7


class ProjectType(Enum):
    mod = 1
    modpack = 2


class VersionType(Enum):
    release = 1
    beta = 2
    alpha = 3


class Role(Enum):
    admin = 1
    moderator = 2
    developer = 3


class Permissions(IntFlag):
    upload_version = 1 << 0
    delete_version = 1 << 1
    edit_details = 1 << 2
    edit_body = 1 << 3
    manage_invites = 1 << 4
    remove_member = 1 << 5
    edit_member = 1 << 6
    delete_project = 1 << 7
    all = 0b11111111


@dataclass
class ModrinthModel:
    """
    The base class for all models.
    """

    @staticmethod
    def _handle_model(value: dict, model_type: Type["ModrinthModel"]) -> "ModrinthModel":
        return model_type.from_data(value)

    @staticmethod
    def _handle_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.strip('Z'))

    @staticmethod
    def _handle_enum(value: int | str, enum_type: Type[Enum]) -> Enum:
        if issubclass(enum_type, IntFlag) and isinstance(value, int):
            return enum_type(value)

        return enum_type[value]

    @staticmethod
    def _handle_generic_container(value, generic_container_type: GenericAlias):
        alias_origin = generic_container_type.__origin__

        if alias_origin is list:
            if not isinstance(value, list):
                raise TypeError(f"Expected type is a list, but {value} is {type(value).__name__}")

            list_types = generic_container_type.__args__

            if len(list_types) != 1:
                raise RuntimeError("List type has more than one type")

            list_type = list_types[0]
            list_type_is_class = isclass(list_type)

            if list_type_is_class and issubclass(list_type, ModrinthModel):
                return [ModrinthModel._handle_model(item, list_type) for item in value]

            elif list_type_is_class and issubclass(list_type, Enum):
                return [ModrinthModel._handle_enum(item, list_type) for item in value]

            elif list_type is datetime:
                return [ModrinthModel._handle_datetime(item) for item in value]

            elif isinstance(list_type, GenericAlias):
                return [ModrinthModel._handle_generic_container(item, list_type) for item in value]

            elif isinstance(list_type, UnionType):
                # noinspection PyProtectedMember
                return [ModrinthModel._handle_union_type(item, list_type) for item in value]

            else:
                return [list_type(item) for item in value]

        else:
            raise RuntimeError(f"{alias_origin.__name__} is not a supported container type")

    @staticmethod
    def _handle_union(value: dict | str | None, union_type: UnionType):
        if value is None:
            return None

        for type_ in union_type.__args__:
            type_is_class = isclass(type_)
            if type_is_class and issubclass(type_, ModrinthModel):
                with suppress():
                    return ModrinthModel._handle_model(value, type_)

            elif type_ is datetime:
                with suppress():
                    return ModrinthModel._handle_datetime(value)

            elif type_is_class and issubclass(type_, Enum):
                with suppress():
                    return ModrinthModel._handle_enum(value, type_)

            elif isinstance(type_, UnionType):
                with suppress():
                    return ModrinthModel._handle_union(value, type_)

            elif isinstance(type_, GenericAlias):
                with suppress():
                    return ModrinthModel._handle_generic_container(value, type_)

            else:
                with suppress():
                    return type_(value)

    @classmethod
    def from_data(cls, data: dict):
        """
        Loads the model from a dictionary.
        """
        for key, value in data.items():
            if key not in cls.__dataclass_fields__:
                raise AttributeError(f"{key} is not a valid attribute of {cls.__name__}")

            # some dumb issue makes match not work
            type_to_match = cls.__dataclass_fields__[key].type
            is_class = isclass(type_to_match)

            if type_to_match is None:
                pass

            elif is_class and issubclass(type_to_match, ModrinthModel):
                data[key] = cls._handle_model(value, type_to_match)

            elif type_to_match is datetime:
                data[key] = cls._handle_datetime(value)

            elif is_class and issubclass(type_to_match, Enum):
                data[key] = cls._handle_enum(value, type_to_match)

            elif isinstance(type_to_match, GenericAlias):
                data[key] = cls._handle_generic_container(value, type_to_match)

            elif isinstance(type_to_match, UnionType):
                data[key] = cls._handle_union(value, type_to_match)

            else:
                data[key] = cls.__dataclass_fields__[key].type(value)

        # noinspection PyArgumentList
        return cls(**data)


@dataclass
class LicenseDescriptor(ModrinthModel):
    """
    A license descriptor.
    """

    id: str
    name: str
    url: str


@dataclass
class DonationDescriptor(ModrinthModel):
    """
    A donation descriptor.
    """

    id: str
    platform: str
    url: str


@dataclass
class DependencyDescriptor(ModrinthModel):
    """
    A dependency descriptor.
    """

    version_id: str
    project_id: str
    dependency_type: str


@dataclass
class HashDescriptor(ModrinthModel):
    """
    A hash descriptor.
    """

    sha512: str
    sha1: str


@dataclass
class FileDescriptor(ModrinthModel):
    """
    A file descriptor.
    """

    hashes: HashDescriptor
    url: str
    filename: str
    primary: bool


@dataclass
class ModeratorMessage(ModrinthModel):
    """
    A moderator message.
    """

    message: str
    body: str | None


@dataclass
class GalleryImage(ModrinthModel):
    """
    A gallery image.
    """

    url: str
    featured: bool
    title: str | None
    description: str | None
    created: datetime


@dataclass
class ProjectModel(ModrinthModel):
    """
    A model for a project.
    """

    slug: str
    title: str
    description: str
    categories: list[str]
    client_side: Requirement
    server_side: Requirement
    body: str
    # TODO: this is deprecated, handle differently
    body_url: None
    status: Status
    license: LicenseDescriptor
    issues_url: str | None
    source_url: str | None
    wiki_url: str | None
    discord_url: str | None
    donation_urls: list[DonationDescriptor] | None
    project_type: ProjectType
    downloads: int
    icon_url: str | None
    id: str
    team: str
    moderator_message: ModeratorMessage | None
    published: datetime
    updated: datetime
    followers: int
    versions: list[str]
    gallery: list[GalleryImage] | None


@dataclass
class SearchResultModel(ModrinthModel):
    """
    A model for a search result.
    """

    slug: str
    title: str
    description: str
    categories: list[str]
    client_side: Requirement
    server_side: Requirement
    project_type: ProjectType
    downloads: int
    icon_url: str | None
    project_id: str
    author: str
    versions: list[str]
    follows: int
    date_created: datetime
    date_modified: datetime
    latest_version: str
    license: str
    gallery: list[str]


@dataclass
class VersionModel(ModrinthModel):
    """
    A model for a version.
    """

    name: str
    version_number: str
    changelog: str
    # TODO: this is deprecated, handle differently
    changelog_url: None
    dependencies: list[DependencyDescriptor]
    game_versions: list[str]
    version_type: VersionType
    loaders: list[str]
    featured: bool
    id: str
    project_id: str
    author_id: str
    date_published: datetime
    downloads: int
    files: list[FileDescriptor]


@dataclass
class UserModel(ModrinthModel):
    """
    A model for a user.
    """

    username: str
    name: str | None
    email: str | None
    bio: str | None
    id: str
    github_id: str | None
    avatar_url: str | None
    created: datetime
    role: Role


@dataclass
class TeamMemberModel(ModrinthModel):
    """
    A model for a team member.
    """

    team_id: str
    user: UserModel
    role: str
    permissions: Permissions | None
    # TODO: can this be None? (when not authenticated)
    accepted: bool
