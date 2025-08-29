from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.views import View
from datetime import date
from .models import (
Episodio, Letto, Paziente, ParametroVitale, DiarioIgiene, Prescrizione, RigaPrescrizione,
 Farmaco, Somministrazione, ContattoEmergenza, Allergia, MenuPeriodo, Pasto,
 PianoTurniPeriodo, Dipendente, RuoloDipendente, PianoTurniPeriodo, AssegnazioneTurno,
 Pietanza, RecapitoContatto)
from django.forms.widgets import ClearableFileInput
from django.forms.models import BaseInlineFormSet


class PazienteForm(forms.ModelForm):
    class Meta:
        model = Paziente
        fields = [
            "nome", "cognome", "sesso", "data_nascita",
            "codice_fiscale", "tessera_sanitaria",
            "telefono", "email",
            # nuovi:
            "comune_nascita", "provincia_nascita",
            "comune_residenza", "provincia_residenza",
            "indirizzo_via", "indirizzo_civico", "indirizzo_cap",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "input"}),
            "cognome": forms.TextInput(attrs={"class": "input"}),
            "sesso": forms.Select(attrs={"class": "select"}),
            "data_nascita": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "codice_fiscale": forms.TextInput(attrs={"class": "input", "style": "text-transform: uppercase;"}),
            "tessera_sanitaria": forms.TextInput(attrs={"class": "input", "style": "text-transform: uppercase;"}),
            "telefono": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
            "comune_nascita": forms.TextInput(attrs={"class": "input"}),
            "provincia_nascita": forms.TextInput(attrs={"class": "input", "maxlength": 2}),
            "comune_residenza": forms.TextInput(attrs={"class": "input"}),
            "provincia_residenza": forms.TextInput(attrs={"class": "input", "maxlength": 2}),
            "indirizzo_via": forms.TextInput(attrs={"class": "input"}),
            "indirizzo_civico": forms.TextInput(attrs={"class": "input", "maxlength": 10}),
            "indirizzo_cap": forms.TextInput(attrs={"class": "input", "maxlength": 5}),
        }

    # normalizzazioni/validazioni leggere
    def clean_codice_fiscale(self):
        cf = (self.cleaned_data.get("codice_fiscale") or "").strip().upper()
        return cf

    def clean_tessera_sanitaria(self):
        ts = self.cleaned_data.get("tessera_sanitaria")
        return ts.strip().upper() if ts else ts

    def clean_nome(self):
        return (self.cleaned_data.get("nome") or "").strip()

    def clean_cognome(self):
        return (self.cleaned_data.get("cognome") or "").strip()

    def clean_provincia_nascita(self):
        val = (self.cleaned_data.get("provincia_nascita") or "").strip().upper()
        if val and (len(val) != 2 or not val.isalpha()):
            raise ValidationError("La provincia deve essere di 2 lettere.")
        return val

    def clean_provincia_residenza(self):
        val = (self.cleaned_data.get("provincia_residenza") or "").strip().upper()
        if val and (len(val) != 2 or not val.isalpha()):
            raise ValidationError("La provincia deve essere di 2 lettere.")
        return val

    def clean_indirizzo_cap(self):
        cap = (self.cleaned_data.get("indirizzo_cap") or "").strip()
        if cap and (len(cap) != 5 or not cap.isdigit()):
            raise ValidationError("CAP non valido (5 cifre).")
        return cap


# --- B) Contatti di emergenza: form + formset con vincolo 'un solo primario' ---
class ContattoEmergenzaForm(forms.ModelForm):
    class Meta:
        model = ContattoEmergenza
        fields = ["nome", "cognome", "relazione", "note", "is_primario", "attivo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "input"}),
            "cognome": forms.TextInput(attrs={"class": "input"}),
            "relazione": forms.Select(attrs={"class": "select"}),
            "note": forms.TextInput(attrs={"class": "input"}),
        }

class BaseContattoEmergenzaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        primari = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE", False):
                continue
            if form.cleaned_data.get("is_primario") and form.cleaned_data.get("attivo", True):
                primari += 1
        if primari > 1:
            raise ValidationError("Puoi selezionare al massimo un contatto primario.")

ContattoEmergenzaFormSet = inlineformset_factory(
    Paziente, ContattoEmergenza,
    form=ContattoEmergenzaForm,
    formset=BaseContattoEmergenzaFormSet,
    extra=2, can_delete=True
)

# --- Recapiti del contatto: form + formset ---
class RecapitoContattoForm(forms.ModelForm):
    class Meta:
        model = RecapitoContatto
        fields = ["tipo", "valore", "preferito", "note"]
        widgets = {
            "tipo": forms.Select(attrs={"class": "select"}),
            "valore": forms.TextInput(attrs={"class": "input"}),
            "note": forms.TextInput(attrs={"class": "input"}),
        }

class BaseRecapitoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Almeno un recapito compilato (telefono o email)
        compilati = 0
        preferiti = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE", False):
                continue
            val = (form.cleaned_data.get("valore") or "").strip()
            if val:
                compilati += 1
                if form.cleaned_data.get("preferito"):
                    preferiti += 1
        if self.total_form_count() and compilati == 0:
            raise ValidationError("Inserisci almeno un recapito (telefono o email).")
        if preferiti > 1:
            raise ValidationError("Puoi selezionare un solo recapito preferito.")

RecapitoFormSet = inlineformset_factory(
    ContattoEmergenza, RecapitoContatto,
    form=RecapitoContattoForm,
    formset=BaseRecapitoFormSet,
    extra=2, can_delete=True
)

# --- C) Allergie: form + formset con coerenza categoria/target e dedup ---
class AllergiaForm(forms.ModelForm):
    class Meta:
        model = Allergia
        fields = ["categoria", "farmaco", "sostanza_libera", "gravita", "reazione", "data_rilevazione", "attiva", "note"]
        widgets = {
            "categoria": forms.Select(attrs={"class": "select"}),
            "farmaco": forms.Select(attrs={"class": "select"}),
            "sostanza_libera": forms.TextInput(attrs={"class": "input"}),
            "gravita": forms.Select(attrs={"class": "select"}),
            "reazione": forms.Textarea(attrs={"class": "input", "rows": 2}),
            "data_rilevazione": forms.DateInput(attrs={"class":"input","type":"date"}),
            "note": forms.TextInput(attrs={"class":"input"}),
        }

    def clean(self):
        cd = super().clean()
        cat = cd.get("categoria")
        farmaco = cd.get("farmaco")
        sost = (cd.get("sostanza_libera") or "").strip()
        if cat == "FARMACO" and not farmaco:
            raise ValidationError("Per allergia farmacologica è necessario indicare il farmaco.")
        if cat in ("ALIMENTARE", "ALTRO") and not sost:
            raise ValidationError("Indica la sostanza/alimento per questa allergia.")
        cd["sostanza_libera"] = sost
        return cd

class BaseAllergiaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        visti = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE", False):
                continue
            cat = form.cleaned_data.get("categoria")
            attiva = form.cleaned_data.get("attiva", True)
            farmaco = form.cleaned_data.get("farmaco")
            sost = (form.cleaned_data.get("sostanza_libera") or "").strip()
            if attiva:
                key = (cat, farmaco.id if farmaco else None, sost.lower())
                if key in visti:
                    raise ValidationError("Allergie duplicate attive nella stessa scheda.")
                visti.add(key)

AllergiaFormSet = inlineformset_factory(
    Paziente, Allergia,
    form=AllergiaForm,
    formset=BaseAllergiaFormSet,
    extra=2, can_delete=True
)
        
class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True
    
class MultipleFileField(forms.FileField):
    widget = MultipleFileInput
    def clean(self, data, initial=None):
        if data in (None, "", []):
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned = []
        for f in data:
            cleaned.append(super().clean(f, initial))
        return cleaned

class EpisodioForm(forms.ModelForm):

    allegati = MultipleFileField(
        label="Documenti scansionati",
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True})
    )

    
    class Meta:
        model = Episodio
        fields = ["paziente", "data_inizio", "provenienza", "motivo", "medico", "letto"]
        widgets = {
            "paziente": forms.Select(attrs={"class": "select"}),
            "data_inizio": forms.DateInput(attrs={"class": "input", "type": "date"}, format="%d/%m/%Y"),
            "provenienza": forms.Select(attrs={"class": "select"}),
            "motivo": forms.TextInput(attrs={"class": "input"}),
            "medico": forms.Select(attrs={"class": "select"}),
            "letto": forms.Select(attrs={"class": "select"}),
        }

    def clean_data_inizio(self):
        d = self.cleaned_data.get("data_inizio")
        if not d:
            raise ValidationError("La data di inizio è obbligatoria.")
        # Se vuoi impedire date future, sblocca la riga seguente:
        # if d > date.today(): raise ValidationError("La data di inizio non può essere futura.")
        return d

    def clean(self):
        cleaned = super().clean()
        paz = cleaned.get("paziente")
        letto = cleaned.get("letto")

        # 1) Un solo episodio attivo per paziente (messaggio user-friendly)
        if paz and Episodio.objects.filter(paziente=paz, data_fine__isnull=True).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Questo paziente ha già un episodio ATTIVO.")

        # 2) Letto libero (nessun altro episodio attivo su quel letto)
        if letto and Episodio.objects.filter(letto=letto, data_fine__isnull=True).exclude(pk=self.instance.pk).exists():
            self.add_error("letto", "Il letto selezionato è occupato.")
        return cleaned

class ParametroVitaleForm(forms.ModelForm):
    class Meta:
        model = ParametroVitale
        fields = [
            "paziente", "rilevato_il",
            "pas", "pad", "fc", "spo2", "temp_c", "glicemia_mgdl",
            "variazione_terapia", "note",
        ]
        widgets = {
            "paziente": forms.Select(attrs={"class": "select"}),
            "rilevato_il": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}),
            "pas": forms.NumberInput(attrs={"class": "input", "min": 50, "max": 260, "step": 1}),
            "pad": forms.NumberInput(attrs={"class": "input", "min": 30, "max": 160, "step": 1}),
            "fc":  forms.NumberInput(attrs={"class": "input", "min": 20, "max": 220, "step": 1}),
            "spo2": forms.NumberInput(attrs={"class": "input", "min": 50, "max": 100, "step": 1}),
            "temp_c": forms.NumberInput(attrs={"class": "input", "min": 30, "max": 45, "step": 0.1}),
            "glicemia_mgdl": forms.NumberInput(attrs={"class": "input", "min": 20, "max": 600, "step": 1}),
            "variazione_terapia": forms.TextInput(attrs={"class": "input"}),
            "note": forms.TextInput(attrs={"class": "input"}),
        }

    def clean(self):
        cleaned = super().clean()
        pas, pad = cleaned.get("pas"), cleaned.get("pad")

        # Se inserisci una delle due PA, richiedi anche l’altra
        if (pas is not None) ^ (pad is not None):
            self.add_error("pas", "Inserire sia PA MAX che PA MIN o nessuna.")
            self.add_error("pad", "Inserire sia PA MAX che PA MIN o nessuna.")

        # Almeno un valore clinico o una nota/variazione deve esserci
        any_value = any(
            cleaned.get(k) not in (None, "", [])
            for k in ["pas","pad","fc","spo2","temp_c","glicemia_mgdl","variazione_terapia","note"]
        )
        if not any_value:
            raise ValidationError("Compila almeno un parametro o una nota.")
        return cleaned

class DiarioIgieneForm(forms.ModelForm):
    class Meta:
        model = DiarioIgiene
        fields = ["paziente", "rilevato_il", "evento"]
        widgets = {
            "paziente": forms.Select(attrs={"class": "select"}),
            "rilevato_il": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}),
            "evento": forms.Select(attrs={"class": "select"}),
        }

class PrescrizioneForm(forms.ModelForm):
    class Meta:
        model = Prescrizione
        fields = ["paziente", "medico", "data_inizio", "data_fine", "attiva", "note"]
        widgets = {
            "paziente": forms.Select(attrs={"class": "select"}),
            "medico": forms.Select(attrs={"class": "select"}),
            "data_inizio": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "data_fine": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "attiva": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "note": forms.Textarea(attrs={"class": "input", "rows": 2}),
        }

DOW_CHOICES = [("1","Lun"),("2","Mar"),("3","Mer"),("4","Gio"),("5","Ven"),("6","Sab"),("7","Dom")]

class RigaPrescrizioneForm(forms.ModelForm):
    # --- NON-MODEL: select della Forma, modificabile (usata anche come filtro lato JS) ---
    farmaco_forma_vis = forms.ChoiceField(
        label="Forma",
        required=False,
        choices=Farmaco.FormaFarmaco.choices,
        widget=forms.Select(attrs={"class": "select"})
    )

    # --- NON-MODEL: orari (per creare OrarioDose) ---
    orari_txt = forms.CharField(
        label="Orari (es. 08:00,12:00,20:00)",
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "08:00,12:00,20:00"})
    )

    # --- NON-MODEL: giorni della settimana (per OrarioDose) ---
    giorni = forms.MultipleChoiceField(
        label="Giorni",
        required=False,
        choices=DOW_CHOICES,
        initial=[c for c,_ in DOW_CHOICES],
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = RigaPrescrizione
        fields = ["farmaco", "dose_val", "dose_udm", "via", "prn", "note"]  # SOLO campi del modello
        widgets = {
            "farmaco": forms.Select(attrs={"class":"select"}),
            "dose_val": forms.NumberInput(attrs={"class":"input", "step":"0.01"}),
            "dose_udm": forms.TextInput(attrs={"class":"input", "placeholder":"mg / ml ..."}),
            "via": forms.Select(attrs={"class":"select"}),
            "prn": forms.CheckboxInput(attrs={"class":"checkbox"}),
            "note": forms.TextInput(attrs={"class":"input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Etichetta “intelligente” per i farmaci (nome — forza — forma)
        def _lbl(f: Farmaco):
            parti = [f.nome]
            if f.forza_val and f.forza_udm:
                # usa :g per togliere zeri inutili (es. 500 invece di 500.00)
                try:
                    val = f"{float(f.forza_val):g}"
                except Exception:
                    val = str(f.forza_val)
                parti.append(f"{val} {f.forza_udm}")
            if f.forma:
                parti.append(f.get_forma_display())
            return " — ".join(parti)

        self.fields["farmaco"].label_from_instance = _lbl
        self.fields["farmaco"].queryset = (
            Farmaco.objects.all().order_by("nome", "forma", "forza_udm", "forza_val")
        )

        # Inizializza "Forma" se c'è già un farmaco selezionato
        f = None
        if self.is_bound:
            fid = self.data.get(self.add_prefix("farmaco"))  # es. form-0-farmaco
            if fid:
                f = Farmaco.objects.filter(pk=fid).first()
        elif getattr(self.instance, "pk", None):
            f = getattr(self.instance, "farmaco", None)

        if f:
            # ATTENZIONE: qui serve il CODICE (es. "cpr"), non la label!
            self.fields["farmaco_forma_vis"].initial = f.forma or ""

    def clean_orari_txt(self):
        """Valida e normalizza gli orari. Ritorna una lista di stringhe HH:MM."""
        raw = (self.cleaned_data.get("orari_txt") or "").strip()
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        out = []
        for p in parts:
            if len(p) != 5 or p[2] != ":":
                raise forms.ValidationError("Formato orari non valido. Usa HH:MM separati da virgola.")
            hh, mm = p.split(":")
            if not (hh.isdigit() and mm.isdigit()):
                raise forms.ValidationError("Usa solo cifre e ‘:’.")
            h, m = int(hh), int(mm)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise forms.ValidationError("Orario fuori intervallo (00:00–23:59).")
            out.append(p)
        return out

RigaPrescrizioneFormSet = inlineformset_factory(
    Prescrizione,
    RigaPrescrizione,
    form=RigaPrescrizioneForm,
    extra=1,
    can_delete=True,
)

class SomministrazioneForm(forms.ModelForm):
    dose_udm_vis = forms.CharField(
        label="Unità",
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "readonly": "readonly", "tabindex": "-1"})
    )

    forma_vis = forms.ChoiceField(
        label="Forma",
        required=False,
        choices=Farmaco.FormaFarmaco.choices,
        widget=forms.Select(attrs={"class": "select", "readonly": "readonly"})  # ← tolto disabled
    )

    class Meta:
        model = Somministrazione
        fields = [
            "paziente", "riga", "programmata_il", "data_ora",
            "dose_erogata", "dose_udm_vis", "forma_vis", "stato", "note"
        ]
        widgets = {
            "paziente": forms.Select(attrs={"class": "select", "id": "id_sel_paziente"}),
            "riga": forms.Select(attrs={"class": "select", "id": "id_riga"}),
            "programmata_il": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}),
            "data_ora": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}),
            "dose_erogata": forms.NumberInput(attrs={"class": "input", "step": "0.01", "min": "0", "id": "id_dose_erogata"}),
            "stato": forms.Select(attrs={"class": "select", "id": "id_stato"}),
            "note": forms.TextInput(attrs={"class": "input", "id": "id_note"}),
        }
        labels = {
            "dose_erogata": "Dose somministrata",
            "riga": "Prescrizioni",
        }

    def __init__(self, *args, **kwargs):
        paziente_prefiltro = kwargs.pop("paziente_prefiltro", None)
        super().__init__(*args, **kwargs)
        self.fields["stato"].initial = "SOMMINISTRATO"

        # Etichette leggibili per le righe
        self.fields["riga"].label_from_instance = lambda obj: (
            f"{obj.farmaco.nome} – {obj.dose_val} {obj.dose_udm} via {obj.get_via_display()}"
        )

        # Filtra righe
        if paziente_prefiltro:
            qs = RigaPrescrizione.objects.filter(
                prescrizione__paziente=paziente_prefiltro,
                prescrizione__attiva=True
            ).select_related("farmaco", "prescrizione")
        else:
            qs = RigaPrescrizione.objects.none()
        self.fields["riga"].queryset = qs

        # Pre-popola forma/udm/dose se c’è già una riga selezionata
        riga_sel = None
        if self.is_bound:
            rid = self.data.get(self.add_prefix("riga"))
            if rid:
                riga_sel = qs.filter(pk=rid).first()
        elif getattr(self.instance, "pk", None):
            riga_sel = self.instance.riga

        if riga_sel:
            self.fields["dose_udm_vis"].initial = riga_sel.dose_udm
            self.fields["forma_vis"].initial = riga_sel.farmaco.forma
            if not self.is_bound:
                self.fields["dose_erogata"].initial = riga_sel.dose_val
            else:
                self.fields["dose_erogata"].widget.attrs.setdefault("placeholder", str(riga_sel.dose_val))
                
    def clean(self):
        cleaned = super().clean()
        paz = cleaned.get("paziente")
        riga = cleaned.get("riga")
        stato = cleaned.get("stato")
        dose = cleaned.get("dose_erogata")
        data_ora = cleaned.get("data_ora")

        # Coerenza paziente–riga
        if paz and riga and riga.prescrizione.paziente_id != paz.id:
            self.add_error("riga", "La riga selezionata non appartiene al paziente scelto.")

        # Se Somministrato → obbliga data_ora e dose ≥ 0
        if stato == "SOMMINISTRATO":
            if not data_ora:
                self.add_error("data_ora", "Obbligatorio se somministrato.")
            if dose in (None, ""):
                self.add_error("dose_erogata", "Obbligatoria se somministrato.")
            elif dose is not None and dose < 0:
                self.add_error("dose_erogata", "La dose deve essere ≥ 0.")

        return cleaned

class MenuDiarioFilterForm(forms.Form):
    periodo = forms.ModelChoiceField(
        queryset=MenuPeriodo.objects.all().order_by("-data_inizio"),
        label="Periodo", required=True,
        widget=forms.Select(attrs={"class": "select"})
    )
    pasto = forms.ChoiceField(
        choices=[("", "Tutti")] + list(Pasto.choices),
        required=False, label="Pasto",
        widget=forms.Select(attrs={"class": "select"})
    )
    giorno = forms.DateField(
        required=False, label="Giorno",
        widget=forms.DateInput(attrs={"type": "date", "class": "input"})
    )
    settimana_iso = forms.IntegerField(
        required=False, min_value=1, max_value=53, label="Settimana ISO",
        widget=forms.NumberInput(attrs={"class": "input", "placeholder": "1–53"})
    )
    q = forms.CharField(
        required=False, label="Cerca",
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Testo/libera/pietanza"})
    )

class TurniDiarioFilterForm(forms.Form):
    periodo = forms.ModelChoiceField(
        queryset=PianoTurniPeriodo.objects.all().order_by("-data_inizio"),
        label="Periodo", required=True, widget=forms.Select(attrs={"class": "select"})
    )
    dipendente = forms.ModelChoiceField(
        queryset=Dipendente.objects.filter(attivo=True).order_by("cognome","nome"),
        label="Dipendente", required=False, widget=forms.Select(attrs={"class": "select"})
    )
    ruolo = forms.ChoiceField(
        choices=[("", "Tutti")] + list(RuoloDipendente.choices),
        required=False, label="Ruolo", widget=forms.Select(attrs={"class": "select"})
    )
    giorno = forms.DateField(
        required=False, label="Giorno",
        widget=forms.DateInput(attrs={"type": "date", "class": "input"})
    )
    settimana_iso = forms.IntegerField(
        required=False, min_value=1, max_value=53, label="Settimana ISO",
        widget=forms.NumberInput(attrs={"class": "input", "placeholder": "1–53"})
    )
    q = forms.CharField(
        required=False, label="Cerca",
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Note o nome"})
    )

class DipendenteForm(forms.ModelForm):
    class Meta:
        model = Dipendente
        fields = ["cognome", "nome", "ruolo", "attivo"]
        widgets = {
            "cognome": forms.TextInput(attrs={"class": "input"}),
            "nome": forms.TextInput(attrs={"class": "input"}),
            "ruolo": forms.Select(attrs={"class": "select"}),
        }

class PianoTurniPeriodoForm(forms.ModelForm):
    class Meta:
        model = PianoTurniPeriodo
        fields = ["nome", "data_inizio", "data_fine", "note", "stato"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "input"}),
            "data_inizio": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "data_fine": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "note": forms.TextInput(attrs={"class": "input"}),
            "stato": forms.Select(attrs={"class": "select"}),
        }

    def clean(self):
        cleaned = super().clean()
        di, df = cleaned.get("data_inizio"), cleaned.get("data_fine")
        if di and df and df < di:
            self.add_error("data_fine", "La data fine non può precedere la data inizio.")
        return cleaned

class AssegnazioneTurnoForm(forms.ModelForm):
    """Il periodo è fissato dalla URL, non mostrato nel form."""
    class Meta:
        model = AssegnazioneTurno
        fields = ["data", "turno", "dipendente", "note"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "turno": forms.Select(attrs={"class": "select"}),
            "dipendente": forms.Select(attrs={"class": "select"}),
            "note": forms.TextInput(attrs={"class": "input"}),
        }

    def __init__(self, *args, **kwargs):
        self.periodo = kwargs.pop("periodo", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        data = cleaned.get("data")
        dip = cleaned.get("dipendente")
        if self.periodo and data:
            # Data dentro il periodo
            if not (self.periodo.data_inizio <= data <= self.periodo.data_fine):
                self.add_error("data", "La data deve essere compresa nel periodo selezionato.")
            # Un turno al giorno per dipendente nello stesso periodo (match alla constraint DB)
            if dip and AssegnazioneTurno.objects.filter(periodo=self.periodo, data=data, dipendente=dip).exists():
                self.add_error(None, "Questo dipendente ha già un turno in questa data nel periodo.")
        return cleaned
        
class MenuPeriodoForm(forms.ModelForm):
    class Meta:
        model = MenuPeriodo
        fields = ["nome", "data_inizio", "data_fine", "stato", "note"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "input"}),
            "data_inizio": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "data_fine": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "stato": forms.Select(attrs={"class": "select"}),
            "note": forms.TextInput(attrs={"class": "input"}),
        }

    def clean(self):
        cleaned = super().clean()
        di, df = cleaned.get("data_inizio"), cleaned.get("data_fine")
        if di and df and df < di:
            self.add_error("data_fine", "La data fine non può precedere la data inizio.")
        return cleaned
        
class PietanzaForm(forms.ModelForm):
    class Meta:
        model = Pietanza
        fields = ["nome", "categoria", "tag_dieta", "allergeni_note"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "input", "autofocus": True}),
            "categoria": forms.Select(attrs={"class": "select"}),
            "tag_dieta": forms.TextInput(attrs={"class": "input", "placeholder": "es. senza sale, veg, senza lattosio"}),
            "allergeni_note": forms.TextInput(attrs={"class": "input", "placeholder": "es. contiene: latte, glutine"}),
        }
        
class MenuPeriodoSelectForm(forms.Form):
    periodo = forms.ModelChoiceField(
        label="Periodo",
        queryset=MenuPeriodo.objects.all().order_by("-data_inizio"),  # <-- QUI
        widget=forms.Select(attrs={"class": "select"})
    )