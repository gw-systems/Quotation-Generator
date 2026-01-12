# Quotation Builder

A Django-based Quotation Management System for Godamwale.

## Features

- **Quotations:** Create, update, and manage quotations.
- **Dynamic Pricing:** Support for multiple locations with specific pricing tables.
- **Document Generation:** Generate formatted DOCX quotations using the Godamwale template (supports multi-location styling).
- **PDF Generation:** Export quotations to PDF (requires LibreOffice).
- **Email Integration:** Send quotations directly to clients.
- **Client Management:** Manage client details.

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/gw-systems/Quotation-Generator.git
   cd Quotation-Generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Create a `.env` file in the root directory:
   ```ini
   DEBUG=True
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=localhost,127.0.0.1
   EMAIL_HOST_USER=your-email@example.com
   EMAIL_HOST_PASSWORD=your-password
   ```

5. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start Server**
   ```bash
   python manage.py runserver
   ```

## Usage

Access the admin panel at `/admin` or the main dashboard to create quotations.

## License

MIT License. See [LICENSE](LICENSE) file.
