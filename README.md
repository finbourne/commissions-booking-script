![LUSID by Finbourne](https://content.finbourne.com/LUSID_repo.png)

# Commissions Booking Script

## Getting Started

### Command Line Variables

Portfolio scope (*required*):<br> `--scope` or `-s` <br>
example use: `-s portfolio-scope-A` <br>

Portfolio code (*required*):<br> `--code` or `c`<br>
example use: `-c portfolio-code-A`<br>

"To" date (time until transactions should be considered, in datetime string format)(*optional*):<br>
`--datetime-iso` or `-dt` <br>
example use: `-dt "2021-01-27T09:09:38.406917+00:00"`<br>
default value: time now

Days going back from the "To" date for transactions to be considered (*optional*):<br>
`--days-going-back` or `-d` <br>
example use: `-d "30"`<br>
default value: Days since portfolio creation date

### Environment Variables
`FBN_CLIENT_ID`: your-app-client-id (From LUSID developer application) <br>
`FBN_CLIENT_SECRET`: your-client-secret (From LUSID developer application) <br>
`FBN_LUSID_API_URL`: https://{your-domain}.lusid.com/api <br>
`FBN_DRIVE_API_URL`: https://{your-domain}.lusid.com/drive <br>
`FBN_TOKEN_URL`: your-auth-token-url (From LUSID developer application) <br>
`FBN_PASSWORD`: your-lusid-password <br>
`FBN_USERNAME`: your-lusid-username

`FBN_SECRETS_PATH`: Path to the secrets.json file including all the abvoe
## Running in docker

To build the docker image, run:

```
docker build -t commissions-booking-script:0.0.1 .
```

To run the docker image and pass authentication env variables with the `-e` tag:
```
docker run \
-e "FBN_CLIENT_ID=<your-app-client-id>" \
-e "FBN_CLIENT_SECRET=<your-client-secret>" \
-e "FBN_LUSID_API_URL=https://<your-domain>.lusid.com/api" \
-e "FBN_DRIVE_API_URL=https://<your-domain>.lusid.com/drive" \
-e "FBN_TOKEN_URL=<your-auth-token-url> \
-e "FBN_PASSWORD=<your-lusid-password>" \
-e "FBN_USERNAME=<your-lusid-username>" \
commissions-booking-script:0.0.1 -s <portfolio scope> -c <portoflio code>
```

Alternatively, use a secrets.json env variable to authenticate:
```
docker run -e "FBN_SECRETS_PATH=<path-to-secrets.json>" \
commissions-booking-script:0.0.1 -s <portfolio scope> -c <portoflio code>
```

## Running directly with python
When running directly with python, just run the `main.py` file, ensuring that the authentication environment variables and command line variables are passed similarly to how it has been done with docker.


## Contributing

We welcome community participation in our tools. For information on contributing see our article [here](/finbourne/commissions-booking-script/docs)

## Reporting Issues
If you encounter any issues please report these the Github [issues page](https://github.com/finbourne/commissions-booking-script/issues).