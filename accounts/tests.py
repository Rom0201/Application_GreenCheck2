from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from django.urls import reverse

from .models import User


class RegisterTests(TestCase):
    def test_page_inscription_s_affiche(self):
        reponse = self.client.get(reverse('register'))
        self.assertEqual(reponse.status_code, 200)

    def test_inscription_valide_cree_un_utilisateur_avec_mot_de_passe_hashe(self):
        reponse = self.client.post(reverse('register'), {
            'firstname': 'Alice',
            'lastname': 'Dupont',
            'email': 'alice@test.fr',
            'password': 'motdepasse123',
        })
        self.assertRedirects(reponse, reverse('login'))
        user = User.objects.get(email='alice@test.fr')
        self.assertNotEqual(user.password, 'motdepasse123')
        self.assertTrue(check_password('motdepasse123', user.password))
        self.assertEqual(user.role, 'user')

    def test_inscription_refuse_un_champ_vide(self):
        self.client.post(reverse('register'), {
            'firstname': '',
            'lastname': 'Dupont',
            'email': 'alice@test.fr',
            'password': 'motdepasse123',
        })
        self.assertEqual(User.objects.count(), 0)

    def test_inscription_refuse_un_email_deja_utilise(self):
        User.objects.create(
            firstname='Alice', lastname='Dupont',
            email='alice@test.fr', password=make_password('x'), role='user',
        )
        self.client.post(reverse('register'), {
            'firstname': 'Bob',
            'lastname': 'Martin',
            'email': 'alice@test.fr',
            'password': 'autre',
        })
        self.assertEqual(User.objects.filter(email='alice@test.fr').count(), 1)


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            firstname='Alice', lastname='Dupont',
            email='alice@test.fr', password=make_password('motdepasse123'), role='user',
        )

    def test_connexion_valide_ouvre_la_session(self):
        reponse = self.client.post(reverse('login'), {
            'email': 'alice@test.fr',
            'password': 'motdepasse123',
        })
        self.assertRedirects(reponse, reverse('dashboard:dashboard'), fetch_redirect_response=False)
        self.assertEqual(self.client.session['user_id'], self.user.id)

    def test_mauvais_mot_de_passe_refuse(self):
        reponse = self.client.post(reverse('login'), {
            'email': 'alice@test.fr',
            'password': 'mauvais',
        })
        self.assertRedirects(reponse, reverse('login'), fetch_redirect_response=False)
        self.assertNotIn('user_id', self.client.session)

    def test_email_inconnu_refuse(self):
        reponse = self.client.post(reverse('login'), {
            'email': 'inconnu@test.fr',
            'password': 'motdepasse123',
        })
        self.assertRedirects(reponse, reverse('login'), fetch_redirect_response=False)
        self.assertNotIn('user_id', self.client.session)

    def test_dashboard_inaccessible_sans_connexion(self):
        reponse = self.client.get(reverse('dashboard:dashboard'))
        self.assertRedirects(reponse, reverse('login'), fetch_redirect_response=False)

    def test_deconnexion_ferme_la_session(self):
        self.client.post(reverse('login'), {
            'email': 'alice@test.fr',
            'password': 'motdepasse123',
        })
        self.client.get(reverse('logout'))
        reponse = self.client.get(reverse('dashboard:dashboard'))
        self.assertRedirects(reponse, reverse('login'), fetch_redirect_response=False)