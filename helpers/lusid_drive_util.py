import json
import os

import lusid_drive

drive_api_factory = lusid_drive.utilities.ApiClientFactory(
    app_name="get_files_from_drive",
    api_secrets_filename=os.getenv("FBN_SECRETS_PATH")
)

file_api = drive_api_factory.build(lusid_drive.FilesApi)
folder_api = drive_api_factory.build(lusid_drive.FoldersApi)
search_api = drive_api_factory.build(lusid_drive.SearchApi)


def get_file_from_drive(directory_path, input_file_name):
    if not directory_path.startswith("/"):
        directory_path = "/" + directory_path
    search_body = lusid_drive.SearchBody(directory_path, input_file_name)
    response = search_api.search(search_body)
    if len(response.values) == 0:
        raise FileNotFoundError(f"The file with name {input_file_name} in the directory {directory_path} "
                                f"has not been found in Lusid Drive")
    file_id = response.values[0].id

    return file_api.download_file(file_id)


def main():
    # for testing only
    file = get_file_from_drive("CommissionConfig", "commission-config.json")

    with open(file) as json_file:
        data = json.load(json_file)
        print(data)


if __name__ == '__main__':
    main()
