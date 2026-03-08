from conftest import *
import pytest

class TestGeneral:
    def test_main_page(self, client, db):
        response = client.get('/')
        assert response.status_code == 200

    def test_registration_page(self, client, db):
        response = client.get('/register')
        assert response.status_code == 200

    def test_login_page(self, client, db):
        response = client.get('/login')
        assert response.status_code == 200

class TestUser:
    def test_registration(self, client, db):
        response = client.post('/register', data={
            "first_name": "New",
            "last_name": "User",
            "login": "newuser",
            "password": "newpassword",
            "email": "new@user.com",
            "birth_date": "1999-01-01",
            "phone_number": "0987654321",
            "additional_info": ""
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login(self, client, user, db):
        response = client.post('/login', data={
            "login": "testuser",
            "password": "testpassword"
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_logout(self, client, user, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200

    def test_get_user_profile(self, client, user, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.get(f'/users/{user.id}')
        assert response.status_code == 200

    def test_update_user_profile(self, client, user, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.post(f'/users/{user.id}', data={
            "first_name": "UpdatedName",
            "last_name": user.last_name,
            "login": user.login,
            "password": user.password,
            "email": user.email,
            "phone_number": user.phone_number,
            "birth_date": user.birth_date.strftime('%Y-%m-%d'),
            "additional_info": "Updated info"
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_delete_user(self, client, user, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.post(f'/users/{user.id}/delete', follow_redirects=True)
        assert response.status_code == 200

class TestFilm:
    def test_get_film_create_page(self, client, user, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.get('/films/new')
        assert response.status_code == 200

    def test_create_film(self, client, user, country, genre, actor, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.post('/films', data={
            "name": "New Film",
            "date": "2023-01-01",
            "poster": "new_film.jpg",
            "country": country.country_name,
            "genre": genre.genre,
            "actor[]": [str(actor.id)],
            "rating": "9",
            "duration": "150",
            "description": "A new film."
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_get_film_info(self, client, film, db):
        response = client.get(f'/films/{film.id}')
        assert response.status_code == 200

    def test_get_film_edit_page(self, client, user, film, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.get(f'/films/{film.id}/edit')
        assert response.status_code == 200

    def test_update_film(self, client, user, film, country, genre, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.post(f'/films/{film.id}/edit', data={
            "name": "Updated Film Name",
            "date": film.date.strftime('%Y-%m-%d'),
            "poster": film.poster,
            "country": country.country_name,
            "genre": genre.genre,
            "actors": "",
            "description": "Updated description.",
            "rating": "10",
            "duration": "160",
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_delete_film(self, client, user, film, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.post(f'/films/{film.id}/delete', follow_redirects=True)
        assert response.status_code == 200

class TestRating:
    def test_create_film_rating(self, client, user, film, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.post(f'/films/{film.id}/rating', data={
            "grade": "10",
            "description": "Great film!"
        }, follow_redirects=True)
        assert response.status_code == 200

class TestMovieList:
    def test_create_list(self, client, user, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        response = client.post(f'/users/{user.id}/lists', data={"list_name": "My Watchlist"}, follow_redirects=True)
        assert response.status_code == 200

    def test_add_to_list(self, client, user, film, db):
        client.post('/login', data={"login": "testuser", "password": "testpassword"}, follow_redirects=True)
        # Create a list first
        client.post(f'/users/{user.id}/lists', data={"list_name": "My Watchlist"}, follow_redirects=True)
        list_id = 1 # Assuming this is the first list
        response = client.post(f'/films/{film.id}/add_to_list', data={"list_id": str(list_id)}, follow_redirects=True)
        assert response.status_code == 200
