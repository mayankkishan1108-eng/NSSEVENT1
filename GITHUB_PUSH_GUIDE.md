# Push this project to GitHub

## Option 1: Push with Git (recommended)

1. Create a new repository on GitHub named `nss-event-camp-portal`. Leave **Add a README**, **Add .gitignore**, and **Choose a license** unchecked because this project already has its files.
2. Install Git for Windows if `git --version` is not recognized. Then open PowerShell in this project folder.
3. Run these commands, replacing `YOUR-USERNAME` with your GitHub username:

```powershell
git init
git add .
git commit -m "Initial NSS event portal"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/nss-event-camp-portal.git
git push -u origin main
```

Git may open a browser window so you can sign in to GitHub. The `.gitignore` file keeps the generated database, local packages, and Python cache out of the upload.

## Option 2: Upload in the GitHub website

1. Create a new repository named `nss-event-camp-portal`.
2. Open the repository and choose **Add file → Upload files**.
3. Open the downloaded project folder and drag its project contents into the upload area. Include `app.py`, `database.py`, `start_portal.py`, `requirements.txt`, `README.md`, `.gitignore`, `templates`, and `static`.
4. Add the commit message `Initial NSS event portal` and choose **Commit changes**.

Do not upload `.local_packages`, `.pip-tmp`, `instance`, or `__pycache__`; these are local generated files and are excluded by `.gitignore` when using Git.

## Run it after downloading from GitHub

Open a terminal in the downloaded project folder and run:

```text
python start_portal.py
```

See `README.md` for the full usage notes and local run instructions.
