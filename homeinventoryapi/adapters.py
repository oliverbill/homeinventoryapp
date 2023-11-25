from google.cloud import secretmanager

from utils.utils import str_to_dict


class GCloudAdapter:
    @classmethod
    def get_secret(cls, project_id: str, secret_id: str, secret_version: int=1) -> secretmanager.GetSecretRequest:
        """
        Get information about the given secret. This only returns metadata about
        the secret container, not any secret material.
        """

        # Import the Secret Manager client library.
        from google.cloud import secretmanager

        # Create the Secret Manager client.
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret.
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{secret_version}"
        # Get the secret.
        response = client.access_secret_version(request={"name": name})
        decoded = response.payload.data.decode("UTF-8")
        result = str_to_dict(decoded)
        return result

