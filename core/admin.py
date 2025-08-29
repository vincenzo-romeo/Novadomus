from django.contrib import admin
from .models import (
    Paziente, Stanza, Letto, Episodio, Farmaco, Prescrizione, RigaPrescrizione,
    OrarioDose, Somministrazione, ParametroVitale, DiarioIgiene, Documento,
    ContattoEmergenza, RecapitoContatto, Allergia, Pietanza, MenuPeriodo, MenuPasto, VoceMenu,
    Dipendente, TurnoTipo, PianoTurniPeriodo, AssegnazioneTurno
)

class RecapitoContattoInline(admin.TabularInline):
    model = RecapitoContatto
    extra = 1
    fields = ("tipo", "valore", "preferito", "note")
    show_change_link = True

@admin.register(ContattoEmergenza)
class ContattoEmergenzaAdmin(admin.ModelAdmin):
    list_display = ("paziente", "cognome", "nome", "relazione", "is_primario", "attivo")
    list_filter = ("relazione", "is_primario", "attivo")
    search_fields = ("cognome", "nome", "paziente__cognome", "paziente__nome")
    inlines = [RecapitoContattoInline]

@admin.register(Allergia)
class AllergiaAdmin(admin.ModelAdmin):
    list_display = ("paziente", "categoria", "farmaco", "sostanza_libera", "gravita", "attiva")
    list_filter = ("categoria", "gravita", "attiva")
    search_fields = ("paziente__cognome", "paziente__nome", "sostanza_libera", "farmaco__nome")
    autocomplete_fields = ("paziente", "farmaco")

@admin.register(Paziente)
class PazienteAdmin(admin.ModelAdmin):
    list_display = ("cognome", "nome", "sesso", "data_nascita", "codice_fiscale", "tessera_sanitaria", "telefono")
    search_fields = ("cognome", "nome", "codice_fiscale", "tessera_sanitaria", "comune_residenza")
    list_filter = ("sesso",)
    ordering = ("cognome", "nome")

class StanzaAdmin(admin.ModelAdmin):
    list_display = ("nome",)

@admin.register(Letto)
class LettoAdmin(admin.ModelAdmin):
    list_display = ("stanza", "codice")
    list_filter = ("stanza",)

@admin.register(Episodio)
class EpisodioAdmin(admin.ModelAdmin):
    list_display = ("paziente", "data_inizio", "data_fine", "stato", "medico", "letto")
    list_filter = ("stato", "data_inizio", "data_fine")

@admin.register(Farmaco)
class FarmacoAdmin(admin.ModelAdmin):
    list_display = ("nome", "forma", "forza_val", "forza_udm", "produttore")
    list_filter = ("forma", "forza_udm",)
    search_fields = ("nome", "codice_atc", "produttore")
    
@admin.register(DiarioIgiene)
class DiarioIgieneAdmin(admin.ModelAdmin):
    list_display = ("paziente", "evento", "rilevato_il", "operatore")
    list_filter = ("evento", "rilevato_il")
    search_fields = ("paziente__cognome", "paziente__nome")
    autocomplete_fields = ("paziente", "operatore")


class RigaPrescrizioneInline(admin.TabularInline):
    model = RigaPrescrizione
    extra = 1
    fields = ("farmaco", "dose_val", "dose_udm", "via", "prn", "note")
    autocomplete_fields = ("farmaco",)
    show_change_link = True

@admin.register(Prescrizione)
class PrescrizioneAdmin(admin.ModelAdmin):
    list_display = ("paziente", "medico", "data_inizio", "data_fine", "attiva")
    list_filter = ("attiva", "medico")
    search_fields = ("paziente__cognome", "paziente__nome", "medico__first_name", "medico__last_name", "note")
    autocomplete_fields = ("paziente", "medico")
    date_hierarchy = "data_inizio"
    inlines = [RigaPrescrizioneInline]

class OrarioDoseInline(admin.TabularInline):
    model = OrarioDose
    extra = 1
    fields = ("ora", "giorni_settimana")

@admin.register(RigaPrescrizione)
class RigaPrescrizioneAdmin(admin.ModelAdmin):
    list_display = ("prescrizione", "farmaco", "dose_val", "dose_udm", "via", "prn")
    list_filter = ("via", "prn")
    autocomplete_fields = ("prescrizione", "farmaco")
    inlines = [OrarioDoseInline]

# Registrazione semplice per gli altri modelli
admin.site.register(Somministrazione)
admin.site.register(ParametroVitale)
admin.site.register(Documento)

# ---------- Inline ----------
class VoceMenuInline(admin.TabularInline):
    model = VoceMenu
    fields = ("ordine", "pietanza", "descrizione_libera", "note")
    extra = 1
    autocomplete_fields = ("pietanza",)
    ordering = ("ordine", "id")

class MenuPastoInline(admin.TabularInline):
    model = MenuPasto
    fields = ("data", "pasto", "note")
    extra = 0
    ordering = ("data", "pasto")

# ---------- Pietanza ----------
@admin.register(Pietanza)
class PietanzaAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "tag_dieta")
    list_filter = ("categoria",)
    search_fields = ("nome", "tag_dieta", "allergeni_note")
    ordering = ("nome",)

# ---------- MenuPeriodo ----------
@admin.register(MenuPeriodo)
class MenuPeriodoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "data_inizio", "data_fine", "stato")
    list_filter = ("stato",)
    search_fields = ("nome", "note")
    ordering = ("-data_inizio",)
    inlines = (MenuPastoInline,)

    actions = ("pubblica", "metti_in_bozza", "archivia")

    @admin.action(description="Imposta stato: Pubblicato")
    def pubblica(self, request, queryset):
        queryset.update(stato=MenuPeriodo.Stato.PUBB)

    @admin.action(description="Imposta stato: Bozza")
    def metti_in_bozza(self, request, queryset):
        queryset.update(stato=MenuPeriodo.Stato.BOZZA)

    @admin.action(description="Imposta stato: Archiviato")
    def archivia(self, request, queryset):
        queryset.update(stato=MenuPeriodo.Stato.ARCH)

# ---------- MenuPasto ----------
@admin.register(MenuPasto)
class MenuPastoAdmin(admin.ModelAdmin):
    list_display = ("data", "pasto", "periodo", "note")
    list_filter = ("pasto", "periodo")
    date_hierarchy = "data"
    search_fields = ("note",)
    ordering = ("-data", "pasto")
    inlines = (VoceMenuInline,)



# ---- Inline assegnazioni dentro il Periodo ----
class AssegnazioneTurnoInline(admin.TabularInline):
    model = AssegnazioneTurno
    fields = ("data", "turno", "dipendente", "note")
    ordering = ("data", "turno__ordine", "dipendente__cognome")
    extra = 0
    autocomplete_fields = ("dipendente", "turno",)

@admin.register(Dipendente)
class DipendenteAdmin(admin.ModelAdmin):
    list_display = ("cognome", "nome", "ruolo", "attivo")
    list_filter = ("ruolo", "attivo")
    search_fields = ("cognome", "nome")
    ordering = ("cognome", "nome")

@admin.register(TurnoTipo)
class TurnoTipoAdmin(admin.ModelAdmin):
    list_display = ("codice", "nome", "ora_inizio", "ora_fine", "is_riposo", "ordine")
    list_editable = ("ordine",)
    list_filter = ("is_riposo",)
    search_fields = ("codice", "nome")
    ordering = ("ordine", "codice")

@admin.register(PianoTurniPeriodo)
class PianoTurniPeriodoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "data_inizio", "data_fine", "stato")
    list_filter = ("stato",)
    search_fields = ("nome", "note")
    ordering = ("-data_inizio",)
    inlines = (AssegnazioneTurnoInline,)
    actions = ("pubblica", "metti_in_bozza", "archivia")

    @admin.action(description="Imposta stato: Pubblicato")
    def pubblica(self, request, queryset):
        queryset.update(stato=PianoTurniPeriodo.Stato.PUBB)

    @admin.action(description="Imposta stato: Bozza")
    def metti_in_bozza(self, request, queryset):
        queryset.update(stato=PianoTurniPeriodo.Stato.BOZZA)

    @admin.action(description="Imposta stato: Archiviato")
    def archivia(self, request, queryset):
        queryset.update(stato=PianoTurniPeriodo.Stato.ARCH)

@admin.register(AssegnazioneTurno)
class AssegnazioneTurnoAdmin(admin.ModelAdmin):
    list_display = ("data", "turno", "dipendente", "periodo", "note")
    list_filter = ("periodo", "turno", "dipendente")
    date_hierarchy = "data"
    search_fields = ("note", "dipendente__cognome", "dipendente__nome")
    ordering = ("-data", "turno__ordine")
    autocomplete_fields = ("dipendente", "turno", "periodo")
    
    def get_changeform_initial_data(self, request):
        init = super().get_changeform_initial_data(request)
        for k in ("periodo", "dipendente", "turno"):
            if k in request.GET:
                init[k] = request.GET.get(k)
        if "data" in request.GET:
            init["data"] = request.GET.get("data")  # YYYY-MM-DD
        return init