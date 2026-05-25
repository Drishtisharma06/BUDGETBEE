# BudgetBee — Bee Smart with Your Money

BudgetBee is a Flask-based expense and budget management web application that helps users monitor spending, optimize budgets, and visualize financial trends. It uses SQLite for persistent storage and includes a responsive multi-page dashboard.

## Key Features
- Secure user authentication with registration and login
- Add, view, search, filter, sort, and delete expenses
- Expense categories and payment methods for accurate tracking
- Dashboard with recent expenses, total spending, and budget overview
- Analytics page with monthly trends and category spending breakdowns
- Budget management with monthly limits, savings goals, and history snapshots
- Profile page for updating username and password
- CSV export of expense history for offline reporting
- Notification-style messages for budgeting and usage guidance

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the environment:
   - Windows:
     ```powershell
     venv\Scripts\activate
     ```
   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App
1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your browser and visit:
   ```text
   http://127.0.0.1:5000
   ```

## Application Structure
- `app.py` — Flask application, routing, database setup, and business logic
- `requirements.txt` — Python dependencies
- `templates/` — Jinja2 HTML views for each page
- `static/css/` — stylesheet for application layout and UI
- `static/js/` — client-side interaction and chart rendering
- `expense_tracker.db` — local SQLite database created automatically on first run

## Database
The app uses SQLite and automatically creates the database schema on startup. The following tables are included:
- `users`
- `expenses`
- `budgets`
- `monthly_history`


## Configuration
- Update the secret key in `app.py` before deploying to a production environment:
  ```python
  app.config['SECRET_KEY'] = 'change_this_to_a_secure_key'
  ```
- For production use, consider loading the secret key from an environment variable instead of hardcoding it.
  ## 🎯 Use Cases
- Personal expense tracking
- Monthly budget management
- Student finance management
- Household spending analysis
- Flask learning and portfolio project

---

## 🤝 Contribution
Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

## 💡 Tagline
> **BudgetBee — Bee Smart With Your Money 🐝**

## Notes
- This project is ideal for personal budgeting, small finance tracking, or as a learning example for Flask applications.
- The interface is built to support quick expense entry, historical expense review, and budget monitoring.

## License
Add your preferred license information here.
