# Amps Assist

**Description:** Plex Amps Music Download Assistant. 

Amps Assist is a fully automated, Dockerized Python application that seamlessly bridges YouTube Music and your Plex Media Server. It automatically scrapes your personalized YouTube Music mixes, custom playlists, and library, downloads the highest-quality audio, formats the metadata and folder structure specifically for Plexamp, generates `.m3u` playlists, and uses the Plex API to instantly inject them into your live server.

---

## 🌟 Features
* **Automated YT Music Sync:** Scans your YouTube Music account for "Mixed for you", "From the community", and your saved Library playlists.
* **Plex-Perfect Metadata:** Uses `yt-dlp` and `ffmpeg` to download audio, and forcefully applies Plex-required ID3 tags (Title, Artist, Album Artist, Album) and embedded cover art using `mutagen`.
* **Native Plex Structure:** Automatically sorts downloads into a clean `All_Songs/Artist/Album/Song.mp3` directory format.
* **Smart Playlist Generation:** Builds lightweight `.m3u` playlist files using absolute paths specifically mapped for Plex's internal database.
* **Direct Plex API Integration:** Bypasses standard Plex library scans to instantly delete old playlists and upload fresh `.m3u` files directly into the Plex database.
* **Set-and-Forget:** Runs continuously in the background on a 30-minute schedule loop.

---

## 📋 Prerequisites

### System Requirements
* **Docker & Docker Compose:** The entire application runs inside a lightweight Python 3.12 Docker container.
* **SMB/CIFS Share:** A NAS or network drive to store the downloaded music (e.g., TrueNAS).
* **Plex Media Server:** A running Plex server to ingest the files and playlists.

### Dependencies (Handled by Docker)
The application automatically installs the following dependencies during the Docker build process:
* `ffmpeg` (System-level requirement for audio extraction)
* Python Packages: `yt-dlp`, `rich`, `ytmusicapi`, `schedule`, `mutagen`, `setuptools<70.0.0`, `requests`.

---

## ⚙️ Configuration Files

Before running the container, you must set up the following three configuration files in the root of your project:

### 1. `.env` (Environment Variables)
Create a `.env` file to securely store your NAS credentials and Plex API token. 
*Note: `PLEX_M3U_PATH` must be the absolute path as your Plex Server sees it internally (e.g., `/data/music/Playlists`), not the Docker or SMB path.*

`
env
# SMB/NAS Credentials
SMB_USERNAME=Your_SMB_Username
SMB_PASSWORD=Your_SMB_Password

# Plex API Connection
PLEX_URL=http://YOUR_PLEX_IP:32400
PLEX_TOKEN=your_plex_token_here
PLEX_LIBRARY=Music
PLEX_M3U_PATH=/data/music/Playlists
`

### 2.** **`browser.json` (YouTube Music Authentication)

Export your authenticated YouTube Music session headers to a file named** **`browser.json`. This allows the** **`ytmusicapi` to read your private, personalized shelves (like "My Supermix").

### 3.** **`src/config.py`

Open** **`src/config.py` to customize your download parameters:

* `PLAYLIST_IDS`: Add specific YouTube or YouTube Music playlist URLs you want to hard-sync.
* `MAX_SONGS_PER_PLAYLIST`: Limit the number of tracks pulled per mix (Default: 25).
* `NUM_WORKERS`: Set the number of simultaneous download threads (Default: 5).

---

## 🚀 How to Run

Because the application uses an SMB volume mount, make sure your host machine supports** **`cifs` (Linux users may need to run** **`sudo apt-get install cifs-utils`).

1. **Build and Start the Container:** Run the following command in the root directory (where your** **`docker-compose.yml`is located):
   **Bash**

   ```
   docker-compose up -d --build
   ```
2. **Check the Logs:** To watch the scanner, downloader, and Plex API sync in real-time, run:
   **Bash**

   ```
   docker-compose logs -f
   ```
3. **Stopping the Service:**
   **Bash**

   ```
   docker-compose down
   ```

---

## 🧠 How it Works Under the Hood

1. **Init:** The container mounts your SMB share to** **`/app/downloads` securely using your** **`.env` variables.
2. **Scan:** The script authenticates with YouTube Music, scrolls your home feed, and memorizes the dynamic titles of your auto-generated mixes.
3. **Sync:** It cross-references your existing** **`.mp3` files. Missing tracks are downloaded via** **`yt-dlp` and tagged. Existing tracks are instantly skipped.
4. **Build:** Old** **`.m3u` files are wiped, and fresh ones are generated using Plex's absolute directory paths.
5. **Push:** The script contacts your Plex API, triggers a library scan, waits 60 seconds, deletes your outdated Plex playlists, and natively uploads the new** **`.m3u` files.
6. **Sleep:** The container waits 30 minutes and does it all again.