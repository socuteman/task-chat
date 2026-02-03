# iak Task Chat Application

A Flask-based web application designed for communication between doctors and physicists in medical settings. The application facilitates task management and real-time chat for collaborative work on medical cases.

## Purpose and Goals

The iak Task Chat Application serves as a specialized platform for healthcare professionals to collaborate on medical physics tasks. The system enables secure communication between doctors and physicists, streamlines task assignment and tracking, and maintains detailed records of all interactions related to patient care.

## Key Features

- **Secure User Authentication**: Role-based access control with three distinct user roles (Admin, Doctor, Physicist)
- **Task Management System**: Comprehensive system for creating, assigning, and tracking medical physics tasks
- **Real-time Chat Functionality**: Dedicated chat rooms for each task to facilitate immediate communication
- **User Status Tracking**: Online/offline indicators to help team members know when colleagues are available
- **Priority and Status Management**: Tasks can be assigned different priority levels (low, medium, high, urgent) and tracked through various statuses (pending, in_progress, completed, cancelled)
- **Responsive Web Interface**: Works seamlessly across desktop and mobile devices
- **Message Read Receipts**: Track which messages have been read by recipients
- **Administrative Controls**: Full admin panel for user management and system oversight

## User Roles

- **Admin**: Full system access, can manage users, tasks, and system settings
- **Doctor**: Can create and assign tasks to physicists, participate in chats
- **Physicist**: Can receive assigned tasks, update task status, participate in chats

## Technical Architecture

- **Backend**: Python Flask web framework with Flask-Login for authentication
- **Database**: SQLite for lightweight, portable storage
- **Frontend**: HTML/CSS/JavaScript with Bootstrap-inspired styling
- **Security**: Password hashing with Werkzeug security module
- **Deployment**: Standalone executable build capability with PyInstaller

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/socuteman/task-chat.git
cd task-chat
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

- `app.py` - Main Flask application with routing and business logic
- `models.py` - Database models (User, Task, ChatMessage)
- `main.py` - Entry point for the application
- `build_exe.py` - Script for building executable
- `requirements.txt` - Python dependencies
- `static/` - CSS, JavaScript, and image files
- `templates/` - HTML templates
- `instance/` - Directory for SQLite database file (created automatically when the app runs, excluded from repo)

## Core Components

### User Model
- Manages user accounts with username, password hashing, and role assignments
- Tracks last seen timestamp for online status
- Supports relationships with tasks and messages

### Task Model
- Represents medical physics tasks with titles, descriptions, and metadata
- Includes priority levels and status tracking
- Links to assigned doctor and physicist
- Maintains creation, update, and completion timestamps

### ChatMessage Model
- Stores chat communications between users
- Links messages to specific tasks
- Tracks sender, receiver, and read status
- Maintains message creation timestamps

## Security Features

- Passwords are securely hashed using Werkzeug's security module
- Session management with Flask-Login
- Role-based access control for all application features
- Protection against unauthorized access to sensitive data

## Mobile Optimization

The application has been optimized for mobile devices with:
- Responsive design that adapts to different screen sizes
- Touch-friendly interface elements
- Optimized layouts for smaller screens
- Elimination of unnecessary scrolling on login page

## Administrative Capabilities

- Complete user management (creation, modification, deletion)
- Task oversight and management
- System monitoring and statistics
- Password reset functionality

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

- iak Development Team (updated 2026)

## Acknowledgments

- Built with Flask, SQLAlchemy, and Bootstrap-inspired styling
- Inspired by the need for better communication in medical physics environments
- Enhanced with modern web development practices for security and usability

## AI Usage Notice

This project was created with the assistance of artificial intelligence for code generation, refactoring, and documentation. The AI helped optimize the codebase and improve documentation quality.

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](LICENSE) file for details.