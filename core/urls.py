# core/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views
from .views import (
    HomeView,
    DashboardView,
    # Pazienti / Setup
    PazienteCreateView,
    PazientePostCreateSetupView,
    # Episodi / Parametri / Igiene / Terapia
    EpisodioCreateView,
    ParametroVitaleCreateView,
    DiarioIgieneCreateView,
    DiarioIgieneView,
    SomministrazioneCreateView,
    DiarioSomministrazioniView,
    DiarioParametriView,
    # Prescrizioni
    PrescrizioneCreateView,
    PrescrizioniListaView,
    # Menu / Turni
    MenuDiarioView,
    MenuPeriodoCreateView,
    PietanzaCreateView,
    TurniDiarioView,
    PianoTurniPeriodoCreateView,
    TurniPeriodoGestisciView,
    TurniPeriodoSelezionaView,
    # Dipendenti
    DipendenteCreateView,
    # Step 2/3: Contatti & Allergie
    ContattiGestisciView,
    ContattoCreateView,
    ContattoUpdateView,
    AllergieEditView,
    ReportMenuPeriodoSelectView,
    ReportMenuPeriodoPrintView
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # Pazienti
    path("pazienti/nuovo/", PazienteCreateView.as_view(), name="paziente_nuovo"),
    path("pazienti/<int:pk>/setup/", PazientePostCreateSetupView.as_view(), name="paziente_setup"),
    path("pazienti/anagrafica/", views.paziente_anagrafica, name="paziente_anagrafica"),

    # Contatti di emergenza
    path("pazienti/<int:pk>/contatti/", ContattiGestisciView.as_view(), name="contatti_edit"),
    path("pazienti/<int:pk>/contatti/nuovo/", ContattoCreateView.as_view(), name="contatto_nuovo"),
    path("contatti/<int:cid>/modifica/", ContattoUpdateView.as_view(), name="contatto_modifica"),

    # Allergie
    path("pazienti/<int:pk>/allergie/", AllergieEditView.as_view(), name="allergie_edit"),

    # Episodi / Parametri / Igiene / Terapia
    path("episodi/accetta/", EpisodioCreateView.as_view(), name="episodio_accetta"),
    path("parametri/nuovo/", ParametroVitaleCreateView.as_view(), name="parametro_nuovo"),
    path("parametri/diario/", DiarioParametriView.as_view(), name="parametri_diario"),
    path("igiene/nuovo/", DiarioIgieneCreateView.as_view(), name="igiene_nuovo"),
    path("igiene/diario/", DiarioIgieneView.as_view(), name="igiene_diario"),
    path("terapia/somministrazioni/nuova/", SomministrazioneCreateView.as_view(), name="somministrazione_nuova"),
    path("terapia/diario/", DiarioSomministrazioniView.as_view(), name="terapia_diario"),

    # Prescrizioni
    path("prescrizioni/nuova/", PrescrizioneCreateView.as_view(), name="prescrizione_nuova"),
    path("prescrizioni/", PrescrizioniListaView.as_view(), name="prescrizioni_lista"),

    # Menu
    path("menu/diario/", MenuDiarioView.as_view(), name="menu_diario"),
    path("menu/periodi/nuovo/", MenuPeriodoCreateView.as_view(), name="menu_periodo_nuovo"),
    path("menu/pietanze/nuova/", PietanzaCreateView.as_view(), name="pietanza_nuova"),

    # Turni
    path("turni/diario/", TurniDiarioView.as_view(), name="turni_diario"),
    path("turni/periodi/nuovo/", PianoTurniPeriodoCreateView.as_view(), name="turni_periodo_nuovo"),
    path("turni/periodi/<int:pk>/gestisci/", TurniPeriodoGestisciView.as_view(), name="turni_periodo_gestisci"),
    path("turni/periodi/", TurniPeriodoSelezionaView.as_view(), name="turni_periodo_seleziona"),
    # Dipendenti
    path("dipendenti/nuovo/", DipendenteCreateView.as_view(), name="dipendente_nuovo"),
    # Report
    path("report/menu/periodo/", ReportMenuPeriodoSelectView.as_view(), name="report_menu_periodo_select"),
    path("report/menu/periodo/<int:pk>/", ReportMenuPeriodoPrintView.as_view(), name="report_menu_periodo_print"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

