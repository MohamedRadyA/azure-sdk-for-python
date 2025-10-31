# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------
"""Customize generated code here.

Follow our quickstart for examples: https://aka.ms/azsdk/python/dpcodegen/python/customize
"""
import os, re, logging
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, List, Optional, AsyncIterable, Tuple, Union
from azure.core.exceptions import ResourceNotFoundError
from azure.core.tracing.decorator_async import distributed_trace_async
from azure.storage.blob.aio import ContainerClient
from ...models._models import (
    Connection,
    ApiKeyCredentials,
    FileDatasetVersion,
    FolderDatasetVersion,
    PendingUploadRequest,
    PendingUploadResponse,
    PendingUploadType,
)
from ...models._enums import ConnectionType
from ._operations import DatasetsOperations as DatasetsOperationsGenerated
from ._operations import ConnectionsOperations as ConnectionsOperationsGenerated

logger = logging.getLogger(__name__)


class TelemetryOperations:
    """
    .. warning::
        **DO NOT** instantiate this class directly.

        Instead, you should access the following operations through
        :class:`~azure.ai.projects.aio.AIProjectClient`'s
        :attr:`telemetry` attribute.
    """

    _connection_string: Optional[str] = None

    def __init__(self, outer_instance: "azure.ai.projects.aio.AIProjectClient") -> None:  # type: ignore[name-defined]
        self._outer_instance = outer_instance

    @distributed_trace_async
    async def get_application_insights_connection_string(self) -> str:  # pylint: disable=name-too-long
        """Get the Application Insights connection string associated with the Project's Application Insights resource.

        :return: The Application Insights connection string if a the resource was enabled for the Project.
        :rtype: str
        :raises ~azure.core.exceptions.ResourceNotFoundError: An Application Insights connection does not
            exist for this Foundry project.
        """
        if not self._connection_string:

            # TODO: Two REST APIs calls can be replaced by one if we have had REST API for get_with_credentials(connection_type=ConnectionType.APPLICATION_INSIGHTS)
            # Returns an empty Iterable if no connections exits.
            connections: AsyncIterable[Connection] = self._outer_instance.connections.list(
                connection_type=ConnectionType.APPLICATION_INSIGHTS,
            )

            # Note: there can't be more than one AppInsights connection.
            connection_name: Optional[str] = None
            async for connection in connections:
                connection_name = connection.name
                break
            if not connection_name:
                raise ResourceNotFoundError("No Application Insights connection found.")

            connection = (
                await self._outer_instance.connections._get_with_credentials(  # pylint: disable=protected-access
                    name=connection_name
                )
            )

            if isinstance(connection.credentials, ApiKeyCredentials):
                if not connection.credentials.api_key:
                    raise ValueError("Application Insights connection does not have a connection string.")
                self._connection_string = connection.credentials.api_key
            else:
                raise ValueError("Application Insights connection does not use API Key credentials.")

        return self._connection_string


class DatasetsOperations(DatasetsOperationsGenerated):
    """
    .. warning::
        **DO NOT** instantiate this class directly.

        Instead, you should access the following operations through
        :class:`~azure.ai.projects.aio.AIProjectClient`'s
        :attr:`datasets` attribute.
    """

    # Internal helper method to create a new dataset and return a ContainerClient from azure-storage-blob package,
    # to the dataset's blob storage.
    async def _create_dataset_and_get_its_container_client(
        self,
        name: str,
        input_version: str,
        connection_name: Optional[str] = None,
    ) -> Tuple[ContainerClient, str]:

        pending_upload_response: PendingUploadResponse = await self.pending_upload(
            name=name,
            version=input_version,
            pending_upload_request=PendingUploadRequest(
                pending_upload_type=PendingUploadType.BLOB_REFERENCE,
                connection_name=connection_name,
            ),
        )
        output_version: str = input_version

        if not pending_upload_response.blob_reference:
            raise ValueError("Blob reference is not present")
        if not pending_upload_response.blob_reference.credential:
            raise ValueError("SAS credential are not present")
        if not pending_upload_response.blob_reference.credential.sas_uri:
            raise ValueError("SAS URI is missing or empty")

        # For overview on Blob storage SDK in Python see:
        # https://learn.microsoft.com/azure/storage/blobs/storage-quickstart-blobs-python
        # https://learn.microsoft.com/azure/storage/blobs/storage-blob-upload-python

        # See https://learn.microsoft.com/python/api/azure-storage-blob/azure.storage.blob.aio.containerclient?view=azure-python#azure-storage-blob-aio-containerclient-from-container-url
        return (
            ContainerClient.from_container_url(
                container_url=pending_upload_response.blob_reference.credential.sas_uri,  # Of the form: "https://<account>.blob.core.windows.net/<container>?<sasToken>"
            ),
            output_version,
        )

    @distributed_trace_async
    async def upload_file(
        self, *, name: str, version: str, file_path: str, connection_name: Optional[str] = None, **kwargs: Any
    ) -> FileDatasetVersion:
        """Upload file to a blob storage, and create a dataset that references this file.
        This method uses the `ContainerClient.upload_blob` method from the azure-storage-blob package
        to upload the file. Any keyword arguments provided will be passed to the `upload_blob` method.

        :keyword name: The name of the dataset. Required.
        :paramtype name: str
        :keyword version: The version identifier for the dataset. Required.
        :paramtype version: str
        :keyword file_path: The file name (including optional path) to be uploaded. Required.
        :paramtype file_path: str
        :keyword connection_name: The name of an Azure Storage Account connection, where the file should be uploaded.
         If not specified, the default Azure Storage Account connection will be used. Optional.
        :paramtype connection_name: str
        :return: The created dataset version.
        :rtype: ~azure.ai.projects.models.FileDatasetVersion
        :raises ~azure.core.exceptions.HttpResponseError: If an error occurs during the HTTP request.
        """

        pathlib_file_path = Path(file_path)
        if not pathlib_file_path.exists():
            raise ValueError(f"The provided file `{file_path}` does not exist.")
        if pathlib_file_path.is_dir():
            raise ValueError("The provided file is actually a folder. Use method `upload_folder` instead")

        container_client, output_version = await self._create_dataset_and_get_its_container_client(
            name=name,
            input_version=version,
            connection_name=connection_name,
        )

        async with container_client:

            with open(file=file_path, mode="rb") as data:  # TODO: What is the best async options for file reading?

                blob_name = pathlib_file_path.name  # Extract the file name from the path.
                logger.debug(
                    "[upload_file] Start uploading file `%s` as blob `%s`.",
                    file_path,
                    blob_name,
                )

                # See https://learn.microsoft.com/python/api/azure-storage-blob/azure.storage.blob.aio.containerclient?view=azure-python#azure-storage-blob-aio-containerclient-upload-blob
                async with await container_client.upload_blob(name=blob_name, data=data, **kwargs) as blob_client:
                    logger.debug("[upload_file] Done uploading")

                    # Remove the SAS token from the URL (remove all query strings).
                    # The resulting format should be "https://<account>.blob.core.windows.net/<container>/<file_name>"
                    data_uri = urlsplit(blob_client.url)._replace(query="").geturl()

                    dataset_version = await self.create_or_update(
                        name=name,
                        version=output_version,
                        dataset_version=FileDatasetVersion(
                            # See https://learn.microsoft.com/python/api/azure-storage-blob/azure.storage.blob.blobclient?view=azure-python#azure-storage-blob-blobclient-url
                            # Per above doc the ".url" contains SAS token... should this be stripped away?
                            data_uri=data_uri,
                        ),
                    )

        return dataset_version  # type: ignore

    @distributed_trace_async
    async def upload_folder(
        self,
        *,
        name: str,
        version: str,
        folder: str,
        connection_name: Optional[str] = None,
        file_pattern: Optional[re.Pattern] = None,
        **kwargs: Any,
    ) -> FolderDatasetVersion:
        """Upload all files in a folder and its sub folders to a blob storage, while maintaining
        relative paths, and create a dataset that references this folder.
        This method uses the `ContainerClient.upload_blob` method from the azure-storage-blob package
        to upload each file. Any keyword arguments provided will be passed to the `upload_blob` method.

        :keyword name: The name of the dataset. Required.
        :paramtype name: str
        :keyword version: The version identifier for the dataset. Required.
        :paramtype version: str
        :keyword folder: The folder name (including optional path) to be uploaded. Required.
        :paramtype folder: str
        :keyword connection_name: The name of an Azure Storage Account connection, where the file should be uploaded.
         If not specified, the default Azure Storage Account connection will be used. Optional.
        :paramtype connection_name: str
        :keyword file_pattern: A regex pattern to filter files to be uploaded. Only files matching the pattern
         will be uploaded. Optional.
        :paramtype file_pattern: re.Pattern
        :return: The created dataset version.
        :rtype: ~azure.ai.projects.models.FolderDatasetVersion
        :raises ~azure.core.exceptions.HttpResponseError: If an error occurs during the HTTP request.
        """
        path_folder = Path(folder)
        if not Path(path_folder).exists():
            raise ValueError(f"The provided folder `{folder}` does not exist.")
        if Path(path_folder).is_file():
            raise ValueError("The provided folder is actually a file. Use method `upload_file` instead.")

        container_client, output_version = await self._create_dataset_and_get_its_container_client(
            name=name, input_version=version, connection_name=connection_name
        )

        async with container_client:

            # Recursively traverse all files in the folder
            files_uploaded: bool = False
            for root, _, files in os.walk(folder):
                for file in files:
                    if file_pattern and not file_pattern.search(file):
                        continue  # Skip files that do not match the pattern
                    file_path = os.path.join(root, file)
                    blob_name = os.path.relpath(file_path, folder).replace("\\", "/")  # Ensure correct format for Azure
                    logger.debug(
                        "[upload_folder] Start uploading file `%s` as blob `%s`.",
                        file_path,
                        blob_name,
                    )
                    with open(file=file_path, mode="rb") as data:  # Open the file for reading in binary mode
                        # See https://learn.microsoft.com/python/api/azure-storage-blob/azure.storage.blob.aio.containerclient?view=azure-python#azure-storage-blob-aio-containerclient-upload-blob
                        await container_client.upload_blob(name=str(blob_name), data=data, **kwargs)
                    logger.debug("[upload_folder] Done uploading file")
                    files_uploaded = True
            logger.debug("[upload_folder] Done uploaded.")

            if not files_uploaded:
                raise ValueError("The provided folder is empty.")

            # Remove the SAS token from the URL (remove all query strings).
            # The resulting format should be "https://<account>.blob.core.windows.net/<container>"
            # See https://learn.microsoft.com/python/api/azure-storage-blob/azure.storage.blob.aio.containerclient?view=azure-python#azure-storage-blob-aio-containerclient-url
            data_uri = urlsplit(container_client.url)._replace(query="").geturl()

            dataset_version = await self.create_or_update(
                name=name,
                version=output_version,
                dataset_version=FolderDatasetVersion(data_uri=data_uri),
            )

        return dataset_version  # type: ignore


class ConnectionsOperations(ConnectionsOperationsGenerated):
    """
    .. warning::
        **DO NOT** instantiate this class directly.

        Instead, you should access the following operations through
        :class:`~azure.ai.projects.aio.AIProjectClient`'s
        :attr:`connections` attribute.
    """

    @distributed_trace_async
    async def get(self, name: str, *, include_credentials: Optional[bool] = False, **kwargs: Any) -> Connection:
        """Get a connection by name.

        :param name: The name of the resource. Required.
        :type name: str
        :keyword include_credentials: Whether to include credentials in the response. Default is False.
        :paramtype include_credentials: bool
        :return: Connection. The Connection is compatible with MutableMapping
        :rtype: ~azure.ai.projects.models.Connection
        :raises ~azure.core.exceptions.HttpResponseError:
        """

        if include_credentials:
            connection = await super()._get_with_credentials(name, **kwargs)
            if connection.type == ConnectionType.CUSTOM:
                # Why do we do this? See comment in the sync version of this code (file _patch_connections.py).
                setattr(
                    connection.credentials,
                    "credential_keys",
                    {k: v for k, v in connection.credentials.as_dict().items() if k != "type"},
                )

            return connection

        return await super()._get(name, **kwargs)

    @distributed_trace_async
    async def get_default(
        self, connection_type: Union[str, ConnectionType], *, include_credentials: Optional[bool] = False, **kwargs: Any
    ) -> Connection:
        """Get the default connection for a given connection type.

        :param connection_type: The type of the connection. Required.
        :type connection_type: str or ~azure.ai.projects.models.ConnectionType
        :keyword include_credentials: Whether to include credentials in the response. Default is False.
        :paramtype include_credentials: bool
        :return: Connection. The Connection is compatible with MutableMapping
        :rtype: ~azure.ai.projects.models.Connection
        :raises ValueError: If no default connection is found for the given type.
        :raises ~azure.core.exceptions.HttpResponseError:
        """
        connections = super().list(connection_type=connection_type, default_connection=True, **kwargs)
        async for connection in connections:
            return await self.get(connection.name, include_credentials=include_credentials, **kwargs)
        raise ValueError(f"No default connection found for type: {connection_type}.")


__all__: List[str] = [
    "TelemetryOperations",
    "DatasetsOperations",
    "ConnectionsOperations",
]  # Add all objects you want publicly available to users at this package level


def patch_sdk():
    """Do not remove from this file.

    `patch_sdk` is a last resort escape hatch that allows you to do customizations
    you can't accomplish using the techniques described in
    https://aka.ms/azsdk/python/dpcodegen/python/customize
    """
