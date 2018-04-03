# Canvass Analytics Pull Predictions
This project is designed to be run on a schedule, whenever it runs it will call an API, translate the response based on configuration and write the response to a MS SQL Database.

## Prerequisites
You need to have `Python3` installed.  Installing python should also install `pip`, Python Package management tool.
* This application is compatible with Python 3.4.x+, but it is recommended to install the latest version. [Download Python Here](https://www.python.org/downloads/)

## Installing
1. To Install this project pull from this repo with
    On Linux based systems
    ```
    wget --no-check-certificate --content-disposition https://github.com/canvassanalytics/APItoDB/archive/v1.0.0.tar.gz
    ```
    On Windows based system (from PowerShell)
    ```
    Invoke-WebRequest -Uri httpshttps://github.com/canvassanalytics/APItoDB/archive/v1.0.0.zip -OutFile C:\Downloads\APItoDB\v1.0.0.zip
    ```
    Or you can just click the `Download` button above

2. Run the following command to install dependencies
    ```
    pip install -r requirements.txt
    ```

3. Configure the `config.yaml` file (See Configuration section below)

4. Use your OS's scheduling tool to run the prediction.py
    * Windows: Use Task Manager
    * Linux: Use Cron

## Configuration
You will need to update the config.yaml file with your setting for the API and Database
```
api_endpoint: <https://api.canvassanlytics.com/your/endpoint>
api_token: <access token from api provider>
response_to_field:
  - json_response_field_1: Database_Field_1
  - json_response_field_2: Database_Field_2
  - json_response_timestamp: Database_Timestamp
database_timestamp_field: Database_Timestamp
adjust_UTC_to_Local_time: True
sql:
  server: localhost
  database: master
  username: sa
  password: password
  table: TestTable
log_level: DEBUG
```
<b>api_endpoint:</b> The API Endpoint you want call whenever the program is run.

<b>api_token:</b> The access token for the API.  You must get this from the API Provider.

<b>response_to_field:</b> This section allows you to map the Data returned from the API to the the fields you want to store the data in the Database.  Any fields returned by the API that are not in this mapping will be dropped.

```
   - json_response_field_1: Database_Field_1
```
In the example above `json_response_field_1` is the field returned in the API JSON, the contents of this response will be written to the `Database_Field_1` field in the database table.

<b>database_timestamp_field:</b> This is the `DateTime` field in the Database

<b>adjust_UTC_to_Local_time:</b> True/False, Use when the response TimeStamp is in UTC time and you want to adjust to the Local time of the Server running this program.  Setting this value to false will write the TimeStamp as it is returned from the API.

<b>sql:</b> Connection setting for the SQL Server

* <b>server:</b> The hostname of the SQL Server
* <b>database:</b> The name of the Database on the SQL Server
* <b>username:</b> The username to authenticate with the SQL Server
* <b>password:</b> The password to authenticate with the SQL Server
* <br>table:</b> The Table Name to write the data to

<b>log_level:</b> The level which you would like to see log messages (written to the console and to predictions.log in this same directory.  Valid options are `DEBUG`, `INFO`, `ERROR`; in order from most logging to least.