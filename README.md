## today blog what?

3 blogs in a day for recommendation by your interest to slack.

## Running the Service in Docker

To run the service in Docker, follow these steps:

1. **Build the Docker image**:
   ```sh
   docker-compose build
   ```

2. **Run the Docker containers**:
   ```sh
   docker-compose up
   ```

3. **Set environment variables**:
   Ensure you have a `.env` file in the root of the project with the necessary environment variables:
   ```sh
   BASE_URL=<your_base_url>
   ES_CERT_FINGERPRINT=<your_es_cert_fingerprint>
   ES_PASSWORD=<your_es_password>
   SLACK_BOT_TOKEN=<your_slack_bot_token>
   SLACK_CHANNEL=<your_slack_channel>
   ```


## Example

![스크린샷 2024-11-19 오전 7 54 52](https://github.com/user-attachments/assets/44798166-858e-4148-a392-bf67fc43d781)
