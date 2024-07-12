from dataclasses import dataclass
import sqlite3
from config import DB_PATH, MAX_NUM_PLAYLISTS

@dataclass
class Playlist:
    id : int
    author_id : int
    name : str

@dataclass
class DB_Reponse:
    result : bool
    message : str

class Database:
    def __init__(self):
        self.__connection  : sqlite3.Connection = self.__get_connection()
        self.__create_database()

    def __get_connection(self):
        return sqlite3.connect(DB_PATH)

    def __create_database(self):
        cursor = self.__connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS PLAYLIST(ID INTEGER PRIMARY KEY AUTOINCREMENT, author_id INTEGER, name varchar(30))")
        cursor.execute("CREATE TABLE IF NOT EXISTS SONG_PLAYLIST(video_id varchar(11), playlist_id INT, PRIMARY KEY(video_id, playlist_id))")
        cursor.close()
        self.__connection.commit()

    def __commit_data(self, sql_str : str) -> bool:
        cursor = self.__connection.cursor()
        res = True
        try:
            cursor.execute(sql_str)
        except sqlite3.IntegrityError:
            res = False
        cursor.close()

        self.__connection.commit()
        return res

    def __select_data(self, sql_str : str) -> list:
        cursor = self.__connection.cursor()
        cursor.execute(sql_str)
        result = cursor.fetchall()
        cursor.close()
        return result
    
    def add_song_to_playlist(self, video_id : str, playlist_name : str, autor_id : int) -> DB_Reponse:
        """Adds a song, identified by its youtube video_id, into a playlist identified by its playlist_id in the database"""

        ids = self.__select_data(sql_str = f"select id from playlist where author_id = {autor_id} and name = '{playlist_name}'")

        if not ids:
            return False
        
        playlist_id = ids[0][0]
        added = self.__commit_data(sql_str = f"INSERT INTO SONG_PLAYLIST (video_id, playlist_id) VALUES ('{video_id}', {playlist_id})")

        return DB_Reponse(result = added, message = f"Added song to **{playlist_name}**." if added else f"Song already exists in **{playlist_name}**.")
    
    def create_playlist(self, playlist_name : str, author_id : int) -> DB_Reponse:
        """Creates a playlist for author_id; checks if it exists already; limited to MAX_NUM_PLAYLISTS."""
        if self.get_playlists(author_id = author_id, playlist_name = playlist_name):
            return DB_Reponse(result = False, message = f"Playlist **{playlist_name}** already exists.")
        
        if len(self.get_playlists(author_id = author_id)) > MAX_NUM_PLAYLISTS:
            return DB_Reponse(result = False, message = f"You have reached the maximum number of playlists.")

        created = self.__commit_data(sql_str = f"INSERT INTO PLAYLIST (author_id, name) VALUES ({author_id},'{playlist_name}')")

        return DB_Reponse(result = created, message = f"Created playlist **{playlist_name}**." if created else f"Failed to create **{playlist_name}**. I do not know why.")
    
    def delete_playlist(self, playlist_name : str, author_id : int) -> DB_Reponse:
        """Deletes a playlist given its playlist_id in the database"""

        playlists = self.get_playlists(author_id = author_id, playlist_name = playlist_name)
        if not playlists:
            return DB_Reponse(result = False, message = f"Playlist **{playlist_name}** does not exist.")
        
        playlist = playlists[0]

        deleted = self.__commit_data(sql_str = f"delete from song_playlist where playlist_id = {playlist.id}")
        if deleted:
            deleted = self.__commit_data(sql_str = f"delete from playlist where id = {playlist.id}")
        
        return DB_Reponse(result = deleted, message = f"Deleted playlist **{playlist_name}**." if deleted else f"Failed to delete playlist **{playlist_name}**. I do not know why.")
    
    def delete_song_from_playlist(self, video_id : str, playlist_name : str, autor_id : int) -> DB_Reponse:
        """Removes a song, identified by its youtube video_id, from a playlist identified by its playlist_id in the database"""
        ids = self.__select_data(sql_str = f"select id from playlist where author_id = {autor_id} and name = '{playlist_name}'")

        if not ids:
            return DB_Reponse(result = False, message = f"Song does not exist in playlist **{playlist_name}**.")

        playlist_id = ids[0][0]
        deleted = self.__commit_data(sql_str = f"delete from SONG_PLAYLIST where video_id = '{video_id}' and playlist_id = {playlist_id}")
        return DB_Reponse(result = deleted, message = f"Deleted song from **{playlist_name}**." if deleted else f"Failed to delete song from playlist **{playlist_name}**. I do not know why.")
    
    def get_playlists(self, author_id : int, playlist_name : str = None, ordered : bool = True) -> list[Playlist]:
        """Returns a list of playlists from author_id"""
        sql = f"SELECT ID, name FROM PLAYLIST where author_id = {author_id}"

        if playlist_name:
            sql = f"{sql} and name = '{playlist_name}'"

        if ordered:
            sql = f"{sql} order by name"
        
        res = self.__select_data(sql_str = sql)

        return [Playlist(id = row[0], author_id = author_id, name = row[1]) for row in res]

    def get_songs_from_playlist(self, author_id : int, playlist_name : str) -> list[str]:
        """Returns a list of video_ids from a playlist given its playlist_id in the database"""      
        sql = f"Select video_id from SONG_PLAYLIST where playlist_id = (select id from playlist where author_id = {author_id} and name = '{playlist_name}')"
        res = self.__select_data(sql_str = sql)
        
        return [v[0] for v in res]
    
    def playlist_exists(self, author_id : int, playlist_name : str) -> bool:
        return self.get_playlists(author_id = author_id, playlist_name = playlist_name) is not None

    def rename_playlist(self, author_id : int, old_name : str, new_name : str) -> DB_Reponse:
        """Renames a playlist identified by its old_name in the database"""
        if not self.playlist_exists(author_id = author_id, playlist_name = old_name):
            return DB_Reponse(result = False, message = f"Playlist '{old_name}' does not exist.")
    
        renamed = self.__commit_data(sql_str = f"update playlist set name='{new_name}' where name='{old_name}' and author_id = {author_id}")
        
        return DB_Reponse(result = renamed, message = f"Renamed playlist from **{old_name}** to **{new_name}**." if renamed else f"Failed to rename playlist **{old_name}** to **{new_name}**. I do not know why.")
