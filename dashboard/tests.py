import io
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import requests
from PIL import Image
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from .models import Plant, Exposure, Location, Diagnostic

# Dossier temporaire : les photos de test n'arrivent jamais dans ton vrai dossier media/
MEDIA_TEST = tempfile.mkdtemp()


def faire_image():
    """Fabrique une vraie petite image JPEG en mémoire."""
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'green').save(buffer, format='JPEG')
    return SimpleUploadedFile('feuille.jpg', buffer.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=MEDIA_TEST)
class DashboardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEST, ignore_errors=True)

    def setUp(self):
        self.alice = User.objects.create(
            firstname='Alice', lastname='Dupont',
            email='alice@test.fr', password=make_password('x'), role='user',
        )
        self.bob = User.objects.create(
            firstname='Bob', lastname='Martin',
            email='bob@test.fr', password=make_password('x'), role='user',
        )
        self.exposition = Exposure.objects.create(label='Plein soleil')
        self.lieu = Location.objects.create(label='Salon')
        self.plante = Plant.objects.create(
            name='Tomate de Alice', plant_type='Tomate',
            user=self.alice, exposure=self.exposition, location=self.lieu,
        )
        self.plante_bob = Plant.objects.create(
            name='Cactus secret', plant_type='Cactus',
            user=self.bob, exposure=self.exposition, location=self.lieu,
        )
        self.connecter(self.alice)

    def connecter(self, user):
        session = self.client.session
        session['user_id'] = user.id
        session.save()

    def test_dashboard_affiche_seulement_les_plantes_de_l_utilisateur(self):
        reponse = self.client.get(reverse('dashboard:dashboard'))
        self.assertContains(reponse, 'Tomate de Alice')
        self.assertNotContains(reponse, 'Cactus secret')

    def test_ajout_plante_valide(self):
        self.client.post(reverse('dashboard:add_plant'), {
            'name': 'Basilic',
            'plant_type': 'Aromatique',
            'exposure': self.exposition.id,
            'location': self.lieu.id,
        })
        plante = Plant.objects.get(name='Basilic')
        self.assertEqual(plante.user, self.alice)

    def test_ajout_plante_sans_nom_refuse(self):
        self.client.post(reverse('dashboard:add_plant'), {
            'name': '',
            'plant_type': 'Aromatique',
            'exposure': self.exposition.id,
            'location': self.lieu.id,
        })
        self.assertEqual(Plant.objects.filter(user=self.alice).count(), 1)

    def test_diagnostic_sur_la_plante_d_un_autre_utilisateur_donne_404(self):
        reponse = self.client.get(reverse('dashboard:add_diagnostic', args=[self.plante_bob.id]))
        self.assertEqual(reponse.status_code, 404)

    def test_diagnostic_refuse_un_faux_fichier_image(self):
        faux = SimpleUploadedFile('faux.jpg', b"ceci n'est pas une image", content_type='image/jpeg')
        self.client.post(reverse('dashboard:add_diagnostic', args=[self.plante.id]), {'image': faux})
        self.assertEqual(Diagnostic.objects.count(), 0)

    def test_diagnostic_refuse_une_mauvaise_extension(self):
        document = SimpleUploadedFile('document.txt', b'texte', content_type='text/plain')
        self.client.post(reverse('dashboard:add_diagnostic', args=[self.plante.id]), {'image': document})
        self.assertEqual(Diagnostic.objects.count(), 0)

    @patch('dashboard.views.requests.post')
    def test_diagnostic_valide_enregistre_le_resultat_du_service_ia(self, mock_post):
        fausse_reponse = MagicMock()
        fausse_reponse.raise_for_status.return_value = None
        fausse_reponse.json.return_value = {
            'result': 'Late blight',
            'plant': 'Tomate',
            'confidence': 0.9999,
            'advice': 'Retire les feuilles atteintes.',
            'warning': None,
        }
        mock_post.return_value = fausse_reponse

        reponse = self.client.post(
            reverse('dashboard:add_diagnostic', args=[self.plante.id]),
            {'image': faire_image()},
        )

        self.assertEqual(reponse.status_code, 302)
        mock_post.assert_called_once()
        diagnostic = Diagnostic.objects.get()
        self.assertEqual(diagnostic.result, 'Late blight')
        self.assertAlmostEqual(diagnostic.confidence, 0.9999)
        self.assertEqual(diagnostic.plant, self.plante)

    @patch('dashboard.views.requests.post', side_effect=requests.exceptions.ConnectionError)
    def test_diagnostic_garde_la_photo_si_le_service_ia_est_indisponible(self, mock_post):
        reponse = self.client.post(
            reverse('dashboard:add_diagnostic', args=[self.plante.id]),
            {'image': faire_image()},
        )
        self.assertEqual(reponse.status_code, 302)
        diagnostic = Diagnostic.objects.get()
        self.assertEqual(diagnostic.result, '')

    def test_suppression_d_une_plante(self):
        self.client.post(reverse('dashboard:delete_plant', args=[self.plante.id]))
        self.assertFalse(Plant.objects.filter(id=self.plante.id).exists())

    def test_suppression_refuse_la_methode_get(self):
        reponse = self.client.get(reverse('dashboard:delete_plant', args=[self.plante.id]))
        self.assertEqual(reponse.status_code, 405)
        self.assertTrue(Plant.objects.filter(id=self.plante.id).exists())

    def test_suppression_de_la_plante_d_un_autre_utilisateur_donne_404(self):
        reponse = self.client.post(reverse('dashboard:delete_plant', args=[self.plante_bob.id]))
        self.assertEqual(reponse.status_code, 404)
        self.assertTrue(Plant.objects.filter(id=self.plante_bob.id).exists())