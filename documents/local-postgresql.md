# Local PostgreSQL setup

PostgreSQL responds on port 5432, but the example `ai_analyst` credentials do not authenticate. No migrations have been applied by this setup step.

In pgAdmin, connect to your existing server using its administrator login. In the Query Tool for the `postgres` database, create a dedicated role and database. Run the statements separately, with auto-commit enabled (`CREATE DATABASE` cannot run inside a transaction):

```sql
CREATE ROLE ai_analyst WITH LOGIN PASSWORD 'choose-your-local-password';
CREATE DATABASE ai_data_analyst OWNER ai_analyst;
```

If the role or database already exists, inspect it rather than recreating or deleting it. You can use the pgAdmin role properties to set the intended password.

Update the repository-root `.env` locally:

```dotenv
POSTGRES_DB=ai_data_analyst
POSTGRES_USER=ai_analyst
POSTGRES_PASSWORD="your-actual-password"
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Use your actual PostgreSQL login, which may differ from the example role. Passwords need no URL encoding. Do not share passwords in chat or commit them. Then run from the repository root:

```powershell
python Project/manage.py migrate
python Project/manage.py runserver
```

Visit `/ready/` to confirm connectivity. The Compose database is an alternative to a local installation; do not start both on the same port.
