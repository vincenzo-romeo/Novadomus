# core/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from datetime import date
User = get_user_model()

class TracciaMixin(models.Model):
    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)
    creato_da = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="creato_%(class)s")
    aggiornato_da = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="aggiornato_%(class)s")
    class Meta:
        abstract = True

# Regex CF (16 caratteri: cognome/nome, data, CIN). Non controlla la validità del carattere di controllo, solo la forma.
_cf_validator = RegexValidator(
    regex=r"^[A-Z]{6}[0-9]{2}[A-EHLMPR-T][0-9]{2}[A-Z][0-9]{3}[A-Z]$",
    message="Inserire un Codice Fiscale valido (16 caratteri, lettere maiuscole)."
)

# Regex tessera sanitaria: 20 cifre, con o senza prefisso IT
_ts_validator = RegexValidator(
    regex=r"^(IT)?\d{20}$",
    message="Inserire un numero tessera sanitaria valido (20 cifre, con o senza prefisso IT)."
)

class Paziente(models.Model):
    SESSO = [
        ("M", "Maschio"),
        ("F", "Femmina"),
        ("X", "Altro/ND"),
    ]

    # Dati base
    nome = models.CharField("Nome", max_length=80)
    cognome = models.CharField("Cognome", max_length=80)
    sesso = models.CharField("Sesso", max_length=1, choices=SESSO)
    data_nascita = models.DateField("Data di nascita")

    # Identificativi
    codice_fiscale = models.CharField(
        "Codice Fiscale",
        max_length=16,
        unique=True,
        validators=[_cf_validator],
    )
    tessera_sanitaria = models.CharField(
        "Tessera Sanitaria",
        max_length=22,  # es. 'IT' + 20 cifre
        unique=True,
        null=True,
        blank=True,
        validators=[_ts_validator],
    )

    # Contatti base
    telefono = models.CharField("Telefono", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)

    # Anagrafica estesa (tutti facoltativi)
    comune_nascita = models.CharField("Comune di nascita", max_length=100, blank=True)
    provincia_nascita = models.CharField("Provincia di nascita (sigla)", max_length=2, blank=True)
    comune_residenza = models.CharField("Comune di residenza", max_length=100, blank=True)
    provincia_residenza = models.CharField("Provincia di residenza (sigla)", max_length=2, blank=True)
    indirizzo_via = models.CharField("Indirizzo (via/piazza)", max_length=150, blank=True)
    indirizzo_civico = models.CharField("Numero civico", max_length=10, blank=True)
    indirizzo_cap = models.CharField("CAP", max_length=5, blank=True)

    # Collegamento eventuale all'utente
    utente = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profilo_paziente",
        verbose_name="Utente collegato",
    )

    # Traccia temporale
    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["cognome", "nome"]),
            models.Index(fields=["codice_fiscale"]),
            models.Index(fields=["comune_residenza", "provincia_residenza"]),
        ]
        ordering = ["cognome", "nome"]
        verbose_name = "Paziente"
        verbose_name_plural = "Pazienti"

    def __str__(self):
        return f"{self.cognome} {self.nome}"

    @property
    def eta(self):
        today = date.today()
        return today.year - self.data_nascita.year - (
            (today.month, today.day) < (self.data_nascita.month, self.data_nascita.day)
        )


class Stanza(models.Model):
    nome = models.CharField(max_length=30, unique=True)
    def __str__(self): return self.nome
    
    class Meta:
        verbose_name = "Stanza"
        verbose_name_plural = "Stanze"

class Letto(models.Model):
    stanza = models.ForeignKey(Stanza, on_delete=models.PROTECT, related_name="letti")
    codice = models.CharField(max_length=10)
    class Meta:
        unique_together = [("stanza","codice")]
    def __str__(self): return f"{self.stanza}-{self.codice}"
    
    class Meta:
        verbose_name = "Letto"
        verbose_name_plural = "Letti"

PROVENIENZA = [
    ("DOM", "Domicilio"),
    ("OSP", "Struttura Ospedaliera"),
    ("SOC", "Servizi Sociali"),
    ("ALT", "Altro"),
]

class Episodio(TracciaMixin):
    STATO = [("ATTIVO","In degenza"),("DIMESSO","Dimesso")]
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name="episodi")
    data_inizio = models.DateField()
    data_fine = models.DateField(null=True, blank=True)
    motivo = models.CharField(max_length=200, blank=True)
    medico = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="episodi_medico")
    letto = models.ForeignKey(Letto, null=True, blank=True, on_delete=models.PROTECT)
    stato = models.CharField(max_length=10, choices=STATO, default="ATTIVO")
    provenienza = models.CharField("Provenienza", max_length=3, choices=PROVENIENZA)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["paziente"], condition=models.Q(data_fine__isnull=True), name="unico_episodio_attivo_per_paziente")
        ]
        ordering = ["-data_inizio"]
        verbose_name = "Episodio"
        verbose_name_plural = "Episodi"

class Farmaco(TracciaMixin):
    class FormaFarmaco(models.TextChoices):
        BUST = "bust", "Bustina"
        CPR  = "cpr",  "Compressa"
        F    = "F",    "Fiala"
        FL   = "FL",   "Flacone"
        GTT  = "gtt",  "Gocce"

    VIE = [
        ("Orale","Orale"), ("IM","IM"), ("EV","EV"), ("SC","SC"),
        ("SL","Sublinguale"), ("TOP","Topica"), ("SNG","Sondino naso gastrico"),
        ("PEG","PEG"), ("DEP","DEP"),
    ]

    nome = models.CharField(max_length=120)
    forma = models.CharField(
        max_length=10,  # copre "bust", "cpr", "F", "FL", "gtt"
        choices=FormaFarmaco.choices,
        blank=True,
        help_text="Forma farmaceutica (es. Bustina, Compressa, Fiala, Flacone, Gocce)."
    )
    forma_valida = property(lambda self: self.forma in dict(self.FormaFarmaco.choices))  # opzionale

    forza_val = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    forza_udm = models.CharField(max_length=20, blank=True)
    codice_atc = models.CharField(max_length=10, blank=True)
    produttore = models.CharField(max_length=120, blank=True)

    class Meta:
        indexes = [models.Index(fields=["nome"])]
        unique_together = [("nome", "forma", "forza_val", "forza_udm")]
        verbose_name = "Farmaco"
        verbose_name_plural = "Farmaci"

    def __str__(self):
        return self.nome

class Prescrizione(TracciaMixin):
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name="prescrizioni")
    medico = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="prescrizioni_medico")
    data_inizio = models.DateField()
    data_fine = models.DateField(null=True, blank=True)
    attiva = models.BooleanField(default=True)
    note = models.TextField(blank=True)
    
    def __str__(self):
        rng = f"{self.data_inizio:%d/%m/%Y}"
        if self.data_fine:
            rng += f"→{self.data_fine:%d/%m/%Y}"
        stato = "attiva" if self.attiva else "chiusa"
        med = f" – {self.medico.get_full_name() or self.medico.username}" if self.medico else ""
        return f"{self.paziente} — {rng} ({stato}){med}"
    
    class Meta:
        ordering = ["-data_inizio"]

    class Meta:
        verbose_name = "Prescrizione"
        verbose_name_plural = "Prescrizioni"

class RigaPrescrizione(TracciaMixin):
    VIE = Farmaco.VIE
    prescrizione = models.ForeignKey(Prescrizione, on_delete=models.CASCADE, related_name="righe")
    farmaco = models.ForeignKey(Farmaco, on_delete=models.PROTECT)
    dose_val = models.DecimalField(max_digits=8, decimal_places=2)
    dose_udm = models.CharField(max_length=20)  # mg, ml, gocce...
    via = models.CharField(max_length=5, choices=VIE)
    prn = models.BooleanField(default=False)  # al bisogno
    note = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.farmaco.nome} – {self.dose_val} {self.dose_udm} via {self.get_via_display()}"
    
    class Meta:
        verbose_name = "RigaPrescrizione"
        verbose_name_plural = "RigaPrescrizioni"

class OrarioDose(TracciaMixin):
    riga = models.ForeignKey(RigaPrescrizione, on_delete=models.CASCADE, related_name="orari")
    ora = models.TimeField()
    giorni_settimana = models.CharField(max_length=7, default="1234567")  # "135" = lun, mer, ven
    class Meta:
        unique_together = [("riga","ora","giorni_settimana")]
        verbose_name = "OrarioDose"
        verbose_name_plural = "OrarioDosi"

class Somministrazione(TracciaMixin):
    STATO = [("SOMMINISTRATO","Somministrato"),("RIFIUTATO","Rifiutato"),("SALTATO","Non disp./saltato")]
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name="somministrazioni")
    riga = models.ForeignKey(RigaPrescrizione, on_delete=models.PROTECT, related_name="somministrazioni")
    programmata_il = models.DateTimeField(null=True, blank=True)
    data_ora = models.DateTimeField(null=True, blank=True)
    operatore = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="somministrazioni_operatore")
    dose_erogata = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    stato = models.CharField(max_length=14, choices=STATO)
    note = models.CharField(max_length=200, blank=True)
    class Meta:
        indexes = [models.Index(fields=["paziente","programmata_il"])]
        verbose_name = "Somministrazione"
        verbose_name_plural = "Somministrazioni"
        
class ParametroVitale(TracciaMixin):
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name="parametri")
    rilevato_il = models.DateTimeField()
    pas = models.PositiveSmallIntegerField(null=True, blank=True)   # PA MAX
    pad = models.PositiveSmallIntegerField(null=True, blank=True)   # PA MIN
    fc = models.PositiveSmallIntegerField(null=True, blank=True)    # Battiti/min
    spo2 = models.PositiveSmallIntegerField(null=True, blank=True)  # %
    temp_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    glicemia_mgdl = models.PositiveSmallIntegerField(null=True, blank=True)
    variazione_terapia = models.CharField(max_length=200, blank=True)
    note = models.CharField(max_length=200, blank=True)
    operatore = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="parametri_operatore")
    class Meta:
        indexes = [models.Index(fields=["paziente","rilevato_il"])]
        ordering = ["-rilevato_il"]
        verbose_name = "ParametroVitale"
        verbose_name_plural = "ParametriVitali"
        
class VoceIgiene(TracciaMixin):
    TURNO = [("MATT","Mattina"),("POM","Pomeriggio"),("NOTTE","Notte")]
    TIPO = [("DOCCIA","Doccia/Bagno"),("PARZ","Igiene parziale"),("ORALE","Igiene orale"),
            ("INTIMA","Igiene intima"),("PANN","Cambio presidio"),("RASATURA","Rasatura"),
            ("CAPUNGH","Capelli/Unghie"),("ALTRO","Altro")]
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name="igiene")
    data = models.DateField()
    turno = models.CharField(max_length=5, choices=TURNO)
    tipo = models.CharField(max_length=10, choices=TIPO)
    operatore = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="igiene_operatore")
    note = models.CharField(max_length=200, blank=True)
    class Meta:
        indexes = [models.Index(fields=["paziente","data"])]
        verbose_name = "VoceIgiene"
        verbose_name_plural = "VociIgiene"

class Documento(TracciaMixin):
    TIPO = [("TERAPIA_SETT","Terapia settimanale"),("DIARIO_PARAM","Diario parametri"),
            ("DIARIO_IGIENE","Diario igiene"),("REFERTO","Referto"),("CONSENSO","Consenso"),
            ("ALTRO","Altro")]
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name="documenti")
    episodio = models.ForeignKey(Episodio, null=True, blank=True, on_delete=models.SET_NULL, related_name="documenti")
    tipo = models.CharField(max_length=20, choices=TIPO, default="ALTRO")
    file = models.FileField(upload_to="documenti_paziente/%Y/%m/")
    caricato_da = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="documenti_caricati")
    tag = models.CharField(max_length=120, blank=True)
    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documenti"
        
class DiarioIgiene(models.Model):
    EVENTO_CHOICES = [
        ("DOCCIA", "Doccia"),
        ("DOCCIA_CAPELLI", "Doccia + Capelli"),
    ]

    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name="diari_igiene")
    rilevato_il = models.DateTimeField()
    evento = models.CharField(max_length=20, choices=EVENTO_CHOICES)
    operatore = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-rilevato_il"]
        indexes = [
            models.Index(fields=["paziente", "rilevato_il"]),
        ]
        verbose_name = "DiarioIgiene"
        verbose_name_plural = "DiarioIgiene"
    def __str__(self):
        return f"{self.paziente} - {self.get_evento_display()} ({self.rilevato_il:%d/%m/%Y %H:%M})"
        
class ContattoEmergenza(TracciaMixin):
    class Relazione(models.TextChoices):
        FIGLIO = "FIGLIO", "Figlio/a"
        CONIUGE = "CONIUGE", "Coniuge/Partner"
        FAMILIARE = "FAMILIARE", "Familiare"
        CAREGIVER = "CAREGIVER", "Caregiver"
        ALTRO = "ALTRO", "Altro"

    paziente = models.ForeignKey("Paziente", on_delete=models.CASCADE, related_name="contatti_emergenza")
    nome = models.CharField(max_length=80)
    cognome = models.CharField(max_length=80)
    relazione = models.CharField(max_length=10, choices=Relazione.choices, default=Relazione.FAMILIARE)
    note = models.CharField(max_length=200, blank=True)
    is_primario = models.BooleanField("Contatto principale", default=False)
    attivo = models.BooleanField(default=True)

    class Meta:
        ordering = ["cognome", "nome"]
        verbose_name = "Contatto di emergenza"
        verbose_name_plural = "Contatti di emergenza"
        constraints = [
            # Al massimo un primario per paziente
            models.UniqueConstraint(
                fields=["paziente"],
                condition=models.Q(is_primario=True, attivo=True),
                name="unico_contatto_primario_per_paziente"
            )
        ]

    def __str__(self):
        return f"{self.cognome} {self.nome} ({self.get_relazione_display()})"


class RecapitoContatto(TracciaMixin):
    class Tipo(models.TextChoices):
        MOBILE = "MOBILE", "Cellulare"
        FISSO = "FISSO", "Telefono fisso"
        EMAIL = "EMAIL", "Email"

    contatto = models.ForeignKey(ContattoEmergenza, on_delete=models.CASCADE, related_name="recapiti")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    valore = models.CharField(max_length=120)  # tel/email (validazione a form)
    preferito = models.BooleanField(default=False)
    note = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-preferito", "tipo", "valore"]
        verbose_name = "Recapito"
        verbose_name_plural = "Recapiti"
        indexes = [models.Index(fields=["tipo", "valore"])]

    def __str__(self):
        pref = "★ " if self.preferito else ""
        return f"{pref}{self.get_tipo_display()}: {self.valore}"
        
class Allergia(TracciaMixin):
    class Categoria(models.TextChoices):
        ALIMENTARE = "ALIMENTARE", "Alimentare"
        FARMACO = "FARMACO", "Farmacologica"
        ALTRO = "ALTRO", "Altro"

    class Gravita(models.TextChoices):
        LIEVE = "LIEVE", "Lieve"
        MODERATA = "MODERATA", "Moderata"
        GRAVE = "GRAVE", "Grave"
        ANAFILASSI = "ANAFILASSI", "Anafilassi"

    paziente = models.ForeignKey("Paziente", on_delete=models.CASCADE, related_name="allergie")
    categoria = models.CharField(max_length=12, choices=Categoria.choices)
    farmaco = models.ForeignKey("Farmaco", null=True, blank=True, on_delete=models.PROTECT)
    sostanza_libera = models.CharField("Sostanza/Alimento", max_length=150, blank=True)
    gravita = models.CharField(max_length=10, choices=Gravita.choices, default=Gravita.MODERATA)
    reazione = models.TextField("Reazione/Note cliniche", blank=True)
    data_rilevazione = models.DateField(null=True, blank=True)
    attiva = models.BooleanField(default=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-attiva", "categoria", "gravita"]
        verbose_name = "Allergia"
        verbose_name_plural = "Allergie"
        indexes = [
            models.Index(fields=["paziente", "attiva"]),
            models.Index(fields=["paziente", "categoria"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="allergia_coerenza_categoria",
                check=(
                    # Se FARMACO: serve almeno farmaco OPPURE sostanza_libera
                    (models.Q(categoria="FARMACO") &
                     (models.Q(farmaco__isnull=False) | models.Q(sostanza_libera__gt="")))
                    |
                    # Se ALIMENTARE/ALTRO: serve sostanza_libera
                    (models.Q(categoria__in=["ALIMENTARE", "ALTRO"]) &
                     models.Q(sostanza_libera__gt=""))
                ),
            ),
            models.UniqueConstraint(
                fields=["paziente", "categoria", "farmaco", "sostanza_libera", "attiva"],
                name="unica_allergia_attiva_per_sostanza_o_farmaco",
            ),
        ]

    def __str__(self):
        target = self.farmaco.nome if (self.categoria == "FARMACO" and self.farmaco) else self.sostanza_libera
        return f"{self.get_categoria_display()} – {target} ({self.get_gravita_display()})"

# === MENU / PASTI ===
class Pasto(models.TextChoices):
    COLAZ = "COLAZ", "Colazione"
    MEREN = "MEREN", "Merenda"
    PRANZ = "PRANZ", "Pranzo"
    SPUN  = "SPUN", "Spuntino"
    CENA  = "CENA",  "Cena"

class CategoriaPietanza(models.TextChoices):
    PRIMO = "PRIMO", "Primo"
    SECON = "SECON", "Secondo"
    CONT  = "CONT",  "Contorno"
    UNICO = "UNICO", "Piatto unico"
    FRUTT = "FRUTT", "Frutta"
    DOLCE = "DOLCE", "Dolce"
    BEV   = "BEV",   "Bevanda"
    ALTRO = "ALTRO", "Altro"

class Pietanza(TracciaMixin):
    nome = models.CharField(max_length=120)
    categoria = models.CharField(max_length=6, choices=CategoriaPietanza.choices, default=CategoriaPietanza.ALTRO)
    tag_dieta = models.CharField(
        "Tag dieta (es. senza sale, veg, senza lattosio)",
        max_length=120, blank=True
    )
    allergeni_note = models.CharField("Allergeni/Note", max_length=200, blank=True)

    class Meta:
        ordering = ["nome"]
        indexes = [models.Index(fields=["nome", "categoria"])]
        verbose_name = "Pietanza"
        verbose_name_plural = "Pietanze"

    def __str__(self):
        return self.nome

class MenuPeriodo(TracciaMixin):
    class Stato(models.TextChoices):
        BOZZA = "BOZZA", "Bozza"
        PUBB  = "PUBB",  "Pubblicato"
        ARCH  = "ARCH",  "Archiviato"

    nome = models.CharField(max_length=80, blank=True)
    data_inizio = models.DateField()
    data_fine = models.DateField()
    stato = models.CharField(max_length=5, choices=Stato.choices, default=Stato.BOZZA)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-data_inizio"]
        indexes = [models.Index(fields=["data_inizio", "data_fine", "stato"])]
        verbose_name = "Periodo menu"
        verbose_name_plural = "Periodi menu"

    def __str__(self):
        lab = self.nome or "Menu"
        return f"{lab} {self.data_inizio:%d/%m/%Y}–{self.data_fine:%d/%m/%Y}"

class MenuPasto(TracciaMixin):
    periodo = models.ForeignKey(MenuPeriodo, on_delete=models.CASCADE, related_name="pasti", null=True, blank=True)
    data = models.DateField()
    pasto = models.CharField(max_length=5, choices=Pasto.choices)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["data", "pasto"]
        indexes = [models.Index(fields=["data", "pasto"]), models.Index(fields=["periodo"])]
        # Un singolo pasto per data (livello struttura). Se preferisci consentire bozza+pubblicato sovrapposti, togli questa constraint.
        constraints = [
            models.UniqueConstraint(fields=["data", "pasto"], name="unico_menu_pasto_per_data")
        ]
        verbose_name = "Menu del pasto"
        verbose_name_plural = "Menu dei pasti"

    def __str__(self):
        return f"{self.get_pasto_display()} – {self.data:%d/%m/%Y}"

class VoceMenu(TracciaMixin):
    pasto = models.ForeignKey(MenuPasto, on_delete=models.CASCADE, related_name="voci")
    # Puoi scegliere una pietanza dal catalogo o scrivere libero (gestione manuale veloce)
    pietanza = models.ForeignKey(Pietanza, null=True, blank=True, on_delete=models.PROTECT)
    descrizione_libera = models.CharField(max_length=150, blank=True)
    ordine = models.PositiveSmallIntegerField(default=1)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["pasto__data", "pasto__pasto", "ordine", "id"]
        indexes = [models.Index(fields=["pasto", "ordine"])]
        constraints = [
            models.CheckConstraint(
                name="voce_menu_pietanza_o_testo",
                check=(models.Q(pietanza__isnull=False) | models.Q(descrizione_libera__gt=""))
            )
        ]
        verbose_name = "Voce di menu"
        verbose_name_plural = "Voci di menu"

    def __str__(self):
        label = self.pietanza.nome if self.pietanza else self.descrizione_libera
        return f"{label} ({self.pasto})"

# === TURNI / DIPENDENTI ===
class RuoloDipendente(models.TextChoices):
    OSS = "OSS", "OSS"
    INF = "INF", "Infermiere"
    CUOCO = "CUOCO", "Cuoco"
    PUL = "PUL", "Pulizie"
    COORD = "COORD", "Coordinatore"
    AMM = "AMM", "Amministrativo"
    ALTRO = "ALTRO", "Altro"

class Dipendente(TracciaMixin):
    # opzionale collegamento a User
    utente = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="profilo_dipendente")
    nome = models.CharField(max_length=80)
    cognome = models.CharField(max_length=80)
    ruolo = models.CharField(max_length=6, choices=RuoloDipendente.choices, default=RuoloDipendente.OSS)
    attivo = models.BooleanField(default=True)

    class Meta:
        ordering = ["cognome", "nome"]
        indexes = [models.Index(fields=["cognome", "nome"]), models.Index(fields=["attivo", "ruolo"])]
        verbose_name = "Dipendente"
        verbose_name_plural = "Dipendenti"

    def __str__(self):
        return f"{self.cognome} {self.nome} ({self.get_ruolo_display()})"

class TurnoTipo(TracciaMixin):
    codice = models.CharField(max_length=12, unique=True)     # es. MATT, POM, NOTTE, RIP
    nome = models.CharField(max_length=40)                    # es. 06:30–13:30
    ora_inizio = models.TimeField(null=True, blank=True)
    ora_fine = models.TimeField(null=True, blank=True)
    is_riposo = models.BooleanField(default=False)
    ordine = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["ordine", "codice"]
        verbose_name = "Tipo turno"
        verbose_name_plural = "Tipi turno"

    def __str__(self):
        return self.nome if self.nome else self.codice

class PianoTurniPeriodo(TracciaMixin):
    class Stato(models.TextChoices):
        BOZZA = "BOZZA", "Bozza"
        PUBB  = "PUBB",  "Pubblicato"
        ARCH  = "ARCH",  "Archiviato"

    nome = models.CharField(max_length=80, blank=True)
    data_inizio = models.DateField()
    data_fine = models.DateField()
    stato = models.CharField(max_length=5, choices=Stato.choices, default=Stato.BOZZA)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-data_inizio"]
        indexes = [models.Index(fields=["data_inizio", "data_fine", "stato"])]
        verbose_name = "Periodo turni"
        verbose_name_plural = "Periodi turni"

    def __str__(self):
        lab = self.nome or "Turni"
        return f"{lab} {self.data_inizio:%d/%m/%Y}–{self.data_fine:%d/%m/%Y}"

class AssegnazioneTurno(TracciaMixin):
    periodo = models.ForeignKey(PianoTurniPeriodo, on_delete=models.CASCADE, related_name="assegnazioni")
    data = models.DateField()
    turno = models.ForeignKey(TurnoTipo, on_delete=models.PROTECT, related_name="assegnazioni")
    dipendente = models.ForeignKey(Dipendente, on_delete=models.PROTECT, related_name="assegnazioni")
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["data", "turno__ordine", "dipendente__cognome"]
        indexes = [models.Index(fields=["periodo", "data"]), models.Index(fields=["dipendente", "data"])]
        constraints = [
            # Un solo turno al giorno per dipendente nello stesso periodo
            models.UniqueConstraint(fields=["periodo", "data", "dipendente"], name="un_turno_per_giorno_per_dipendente"),
        ]
        verbose_name = "Assegnazione turno"
        verbose_name_plural = "Assegnazioni turni"

    def __str__(self):
        return f"{self.data:%d/%m/%Y} – {self.turno} – {self.dipendente}"
