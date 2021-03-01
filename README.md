![LUSID by Finbourne](https://content.finbourne.com/LUSID_repo.png)

# Commissions Booking Script

## Getting Started

To build the docker image, run:

```
docker build -t commissions-booking-script:0.0.1 .
```

To run the docker image:
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

Alternatively, use a secrets.json to authenticate:
```
docker run -e "FBN_SECRETS_PATH=<path-to-secrets.json>" \
commissions-booking-script:0.0.1 -s <portfolio scope> -c <portoflio code>
```

### Variables:

Portfolio scope:<br> `--scope` or `-s` <br>
Portfolio code:<br> `--code` or `c`<br>
"To" date (time until transactions should be considered):<br>
`--datetime-iso` or `-dt` <br>
Days going back from the "To" date for transactions to be considered:<br>
`--days-going-back` or `-d` <br>


## Contributing

We welcome community participation in our tools. For information on contributing see our article [here](/finbourne/commissions-booking-script/docs)

## Reporting Issues
If you encounter any issues please report these the Github [issues page](https://github.com/finbourne/commissions-booking-script/issues).