# Power Checker Telegram Bot

A Telegram bot that collects user information and integrates with a backend service for power/electricity checking functionality.

## Features

- User registration with validation
- Collects user information (name, surname, email, phone)
- Periodic backend health checks
- Docker support for easy deployment
- Input validation for email and phone numbers
- Error handling and logging

## Prerequisites

- Python 3.11+
- Docker (optional)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Environment Variables

Copy `sample.env` to `.env` and configure the following variables:

```env
TOKEN=your_telegram_bot_token
BACKEND_URL=your_backend_url
PERIODIC_TASK_URL=your_periodic_task_url
ADMIN_KEY=your_admin_key
```

## Installation

### Local Development

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
python app.py
```

### Docker Deployment

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

## Project Structure

```
├── app.py              # Main bot application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── .env              # Environment variables (not in repo)
├── sample.env        # Sample environment variables
├── .gitignore       # Git ignore rules
└── README.md        # Project documentation
```

## Bot Commands

- `/start` - Start registration process
- `/cancel` - Cancel current operation

## Error Handling

The bot includes comprehensive error handling for:
- Network issues
- Backend service failures
- Invalid input validation
- Environment configuration issues

## Logging

Logs are written to both console and `bot.log` file, including:
- Bot startup/shutdown events
- User interactions
- Backend communication
- Error messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For support, email umuttopalak@hotmail.com or create an issue in the repository.
