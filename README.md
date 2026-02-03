# Task Chat Application

A Flask-based web application designed for communication between doctors and physicists in medical settings. The application facilitates task management and real-time chat for collaborative work on medical cases.

## Features

- User authentication system with role-based access (Admin, Doctor, Physicist)
- Task management system for assigning and tracking medical physics tasks
- Real-time chat functionality for each task
- User status tracking (online/offline indicators)
- Priority and status tracking for tasks
- Responsive web interface

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/socuteman/medical-chat.git
cd medical-chat
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - On Windows:
   ```bash
   venv\Scripts\activate
   ```
   - On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Development Server

1. Navigate to the project directory
2. Run the application:
```bash
python main.py
```

3. Open your browser and go to `http://localhost:5000`
4. Log in with the default admin credentials:
   - Username: `admin`
   - Password: `admin123`

### Default User Accounts

- Admin: `admin` / `admin123`
- Additional users can be created by the admin through the registration interface

### Building Executable

To create a standalone executable version of the application:

```bash
python build_exe.py
```

Or run the batch file on Windows:
```bash
quick_build.bat
```

The executable will be created in the `dist/` folder.
## Project Structure

- `app.py` - Main Flask application
- `models.py` - Database models (User, Task, ChatMessage)
- `main.py` - Entry point for the application
- `build_exe.py` - Script for building executable
- `requirements.txt` - Python dependencies
- `static/` - CSS, JavaScript, and image files
- `templates/` - HTML templates
- `instance/` - Directory for SQLite database file (created automatically when the app runs, excluded from repo)


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
## Release Management

To create a new release:

1. Update the version number:
   ```bash
   python release_manager.py release --version 1.2.3
   ```

2. This will:
   - Update version information in the code
   - Create a release branch named `release/v1.2.3`
   - Generate a version.json file

3. Build the executable:
   ```bash
   python build_exe.py
   ```

4. Test the build thoroughly

5. Push the release branch to GitHub:
   ```bash
   git push origin release/v1.2.3
   ```

Alternatively, you can publish directly to a version branch on GitHub:

```bash
python publish_build.py 1.2.3
```

This will:
- Create a version branch named `v1.2.3`
- Build the executable
- Update version information
- Create a Git tag for the release
- Push everything to GitHub


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- Medical Chat Development Team

## Acknowledgments

- Built with Flask, SQLAlchemy, and Bootstrap
- Inspired by the need for better communication in medical physics environments