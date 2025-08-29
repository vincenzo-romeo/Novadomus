from django.views.generic import TemplateView, CreateView, View, FormView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse, NoReverseMatch
from django.contrib import messages
from datetime import timedelta
from django.utils.dateparse import parse_date
from .models import (
Paziente,ContattoEmergenza, Episodio, Letto, Documento, ParametroVitale, DiarioIgiene, Prescrizione, 
OrarioDose, Somministrazione, ParametroVitale, Farmaco, MenuPeriodo, MenuPasto, 
VoceMenu, Pasto, PianoTurniPeriodo, AssegnazioneTurno, TurnoTipo, Dipendente, PianoTurniPeriodo,
AssegnazioneTurno, Pietanza,)
from .forms import (
PazienteForm, ContattoEmergenzaFormSet, ContattoEmergenzaForm, AllergiaFormSet, EpisodioForm, 
ParametroVitaleForm, DiarioIgieneForm, PrescrizioneForm, RigaPrescrizioneFormSet, MenuPeriodoSelectForm,
SomministrazioneForm, MenuDiarioFilterForm, TurniDiarioFilterForm, DipendenteForm, PianoTurniPeriodoForm, 
AssegnazioneTurnoForm, MenuPeriodoForm, PietanzaForm, RecapitoContatto, RecapitoFormSet)
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from collections import defaultdict
from django.utils import timezone
from datetime import timedelta
import json
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.db.models import Prefetch, Q

def safe_reverse(name, *args, **kwargs):
    try:
        return reverse(name, *args, **kwargs)
    except NoReverseMatch:
        return None

class HomeView(TemplateView):
    template_name = "core/home.html"

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

@method_decorator(csrf_protect, name='dispatch')
class PazienteCreateView(CreateView):
    model = Paziente
    form_class = PazienteForm
    template_name = "core/paziente_form.html"
    success_url = reverse_lazy("dashboard")  
    
    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        ctx = self.get_context_data(form=form)
        return self.render_to_response(ctx)

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            self.object = form.save()
            messages.success(request, "Paziente creato.")
            return HttpResponseRedirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))
            
        
class PazientePostCreateSetupView(LoginRequiredMixin, TemplateView):
    template_name = "core/paziente_setup.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paziente = get_object_or_404(Paziente, pk=kwargs["pk"])

        # placeholder: li attiveremo allo step 2/3
        ctx["url_contatti"] = f"{safe_reverse('contatti_edit', args=[paziente.pk])}?next={safe_reverse('paziente_anagrafica')}"
        ctx["url_allergie"] = f"{safe_reverse('allergie_edit', args=[paziente.pk])}?next={safe_reverse('paziente_anagrafica')}"

        # tenta vari name possibili per il create Episodio
        url_epi = (
            safe_reverse("episodio_nuovo")
            or safe_reverse("episodio_create")
            or safe_reverse("episodio_add")
        )
        if url_epi:
            url_epi = f"{url_epi}?paziente={paziente.pk}"
        ctx["url_episodio"] = url_epi

        # scheda paziente (se manca, fallback dashboard)
        url_scheda = safe_reverse("paziente_anagrafica")
        ctx["url_scheda"] = f"{url_scheda}?p={paziente.pk}" if url_scheda else safe_reverse("dashboard")

        ctx["url_dashboard"] = safe_reverse("dashboard")
        return ctx
        
class AllergieEditView(View):
    template_name = "core/paziente_allergie_formset.html"

    def dispatch(self, request, pk, *args, **kwargs):
        self.paziente = get_object_or_404(Paziente, pk=pk)
        return super().dispatch(request, pk, *args, **kwargs)

    def get(self, request, pk):
        fs = AllergiaFormSet(instance=self.paziente, prefix="allergie")
        return render(request, self.template_name, {
            "paziente": self.paziente, "formset": fs, "next": request.GET.get("next")
        })

    def post(self, request, pk):
        fs = AllergiaFormSet(request.POST, instance=self.paziente, prefix="allergie")
        if fs.is_valid():
            fs.save()
            messages.success(request, "Allergie aggiornate.")
            return redirect(request.POST.get("next") or "paziente_setup", pk=self.paziente.pk)
        messages.error(request, "Correggi gli errori indicati.")
        return render(request, self.template_name, {
            "paziente": self.paziente, "formset": fs, "next": request.POST.get("next")
        })
        
class ContattiGestisciView(View):
    template_name = "core/paziente_contatti_list.html"

    def get(self, request, pk):
        paziente = get_object_or_404(Paziente, pk=pk)
        contatti = paziente.contatti_emergenza.all()
        return render(request, self.template_name, {
            "paziente": paziente, "contatti": contatti
        })

class ContattoCreateView(View):
    template_name = "core/contatto_form.html"

    def get(self, request, pk):
        paziente = get_object_or_404(Paziente, pk=pk)
        form = ContattoEmergenzaForm()
        fs = RecapitoFormSet()  # vuoto, lo compiliamo dopo il salvataggio se preferisci
        return render(request, self.template_name, {"paziente": paziente, "form": form, "formset": fs, "mode": "create"})

    def post(self, request, pk):
        paziente = get_object_or_404(Paziente, pk=pk)
        form = ContattoEmergenzaForm(request.POST)
        if form.is_valid():
            contatto = form.save(commit=False)
            contatto.paziente = paziente
            contatto.save()
            messages.success(request, "Contatto creato.")
            return redirect("contatto_modifica", cid=contatto.pk)  # ora compili i recapiti
        return render(request, self.template_name, {"paziente": paziente, "form": form, "formset": RecapitoFormSet(), "mode": "create"})

class ContattoUpdateView(View):
    template_name = "core/contatto_form.html"

    def get_obj(self, cid):
        return get_object_or_404(ContattoEmergenza.objects.select_related("paziente"), pk=cid)

    def get(self, request, cid):
        contatto = self.get_obj(cid)
        form = ContattoEmergenzaForm(instance=contatto)
        fs = RecapitoFormSet(instance=contatto, prefix="recapiti")
        return render(request, self.template_name, {"paziente": contatto.paziente, "contatto": contatto, "form": form, "formset": fs, "mode": "update"})

    def post(self, request, cid):
        contatto = self.get_obj(cid)
        form = ContattoEmergenzaForm(request.POST, instance=contatto)
        fs = RecapitoFormSet(request.POST, instance=contatto, prefix="recapiti")
        if form.is_valid() and fs.is_valid():
            form.save()
            fs.save()
            messages.success(request, "Contatto aggiornato.")
            # torna alla lista del paziente
            return redirect("contatti_edit", pk=contatto.paziente.pk)
        messages.error(request, "Correggi gli errori indicati.")
        return render(request, self.template_name, {"paziente": contatto.paziente, "contatto": contatto, "form": form, "formset": fs, "mode": "update"})


class EpisodioCreateView(LoginRequiredMixin, CreateView):
    model = Episodio
    form_class = EpisodioForm
    template_name = "core/episodio_form.html"
    success_url = reverse_lazy("dashboard")

    def get_initial(self):
        init = super().get_initial()
        # precompila data odierna
        init["data_inizio"] = timezone.now().date()
        # pre-seleziona paziente se passato come ?paziente=ID
        pid = self.request.GET.get("paziente")
        if pid and Paziente.objects.filter(pk=pid).exists():
            init["paziente"] = pid
        return init

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # mostra solo i letti liberi (nessun episodio ATTIVO associato)
        occupati = Episodio.objects.filter(data_fine__isnull=True, letto__isnull=False).values_list("letto_id", flat=True)
        form.fields["letto"].queryset = Letto.objects.exclude(id__in=occupati)
        form.fields["letto"].required = False  # opzionale: consenti accettazione senza assegnare subito il letto
        return form

    def form_valid(self, form):
        resp = super().form_valid(form)  # salva l'episodio
        files = self.request.FILES.getlist("allegati")
        for f in files:
            Documento.objects.create(
                paziente=form.cleaned_data["paziente"],
                episodio=self.object,
                tipo="ALTRO",           # o "CONSENSO" se preferisci
                file=f,
                caricato_da=self.request.user,
                tag="accettazione"
            )
        return resp

class ParametroVitaleCreateView(LoginRequiredMixin, CreateView):
    model = ParametroVitale
    form_class = ParametroVitaleForm
    template_name = "core/parametro_form.html"
    success_url = reverse_lazy("dashboard")

    def get_initial(self):
        init = super().get_initial()
        init["rilevato_il"] = timezone.now()
        pid = self.request.GET.get("paziente")
        if pid and Paziente.objects.filter(pk=pid).exists():
            init["paziente"] = pid
        return init

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # opzionale: limita ai pazienti con episodio attivo
        attivi = Episodio.objects.filter(data_fine__isnull=True).values_list("paziente_id", flat=True)
        form.fields["paziente"].queryset = Paziente.objects.filter(id__in=attivi) or Paziente.objects.all()
        return form

    def form_valid(self, form):
        form.instance.operatore = self.request.user
        resp = super().form_valid(form)
        messages.success(self.request, "Parametro vitale registrato.")
        return resp
        
class DiarioIgieneCreateView(LoginRequiredMixin, CreateView):
    model = DiarioIgiene
    form_class = DiarioIgieneForm
    template_name = "core/igiene_form.html"
    success_url = reverse_lazy("dashboard")

    def get_initial(self):
        init = super().get_initial()
        init["rilevato_il"] = timezone.now()
        pid = self.request.GET.get("paziente")
        if pid and Paziente.objects.filter(pk=pid).exists():
            init["paziente"] = pid
        return init

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # opzionale: limita a pazienti con episodio attivo
        attivi = Episodio.objects.filter(data_fine__isnull=True).values_list("paziente_id", flat=True)
        form.fields["paziente"].queryset = Paziente.objects.filter(id__in=attivi) or Paziente.objects.all()
        return form

    def form_valid(self, form):
        form.instance.operatore = self.request.user
        resp = super().form_valid(form)
        messages.success(self.request, "Diario igiene salvato.")
        return resp

class PrescrizioneCreateView(LoginRequiredMixin, View):
    template_name = "core/prescrizione_form.html"
    success_url = reverse_lazy("dashboard")

    def _ctx(self, p_form, fs):
        forma_code_map = {}
        for f in Farmaco.objects.all().only("id", "forma"):
            forma_code_map[str(f.id)] = f.forma or ""   # es. "cpr", "bust", "F", ...
        return {
            "form": p_form,
            "formset": fs,
            "farmaci_forma_code_map": json.dumps(forma_code_map),
        }

    def get(self, request):
        p_form = PrescrizioneForm(initial={"data_inizio": timezone.now().date(), "attiva": True})
        fs = RigaPrescrizioneFormSet()
        pid = request.GET.get("paziente")
        if pid:
            p_form.fields["paziente"].initial = pid
        return render(request, self.template_name, self._ctx(p_form, fs))

    def post(self, request):
        p_form = PrescrizioneForm(request.POST)
        fs = RigaPrescrizioneFormSet(request.POST)
        if p_form.is_valid() and fs.is_valid():
            prescrizione = p_form.save(commit=False)
            prescrizione.creato_da = request.user
            prescrizione.aggiornato_da = request.user
            prescrizione.save()
            fs.instance = prescrizione
            righe = fs.save(commit=False)

            from datetime import time

            def parse_orari(raw):
                """Accetta lista già pulita o stringa grezza; restituisce [(h,m), ...]."""
                if not raw:
                    return []
                if isinstance(raw, str):
                    items = [p.strip() for p in raw.split(",") if p.strip()]
                else:
                    items = raw
                out = []
                for p in items:
                    if isinstance(p, str) and len(p) == 5 and p[2] == ":":
                        hh, mm = p.split(":", 1)
                        if hh.isdigit() and mm.isdigit():
                            h, m = int(hh), int(mm)
                            if 0 <= h <= 23 and 0 <= m <= 59:
                                out.append((h, m))
                return out

            # salva righe + genera orari
            for r_form, r_obj in zip(fs.forms, righe):
                r_obj.creato_da = request.user
                r_obj.aggiornato_da = request.user
                r_obj.save()

                orari_pairs = parse_orari(r_form.cleaned_data.get("orari_txt"))
                giorni = r_form.cleaned_data.get("giorni", [])
                giorni_str = "".join(sorted(giorni)) if giorni else "1234567"

                for h, m in orari_pairs:
                    OrarioDose.objects.get_or_create(
                        riga=r_obj,
                        ora=time(h, m),
                        giorni_settimana=giorni_str,
                        defaults={"creato_da": request.user, "aggiornato_da": request.user},
                    )

            for obj in fs.deleted_objects: obj.delete()
            messages.success(request, "Prescrizione salvata.")
            return redirect(self.success_url)

        return render(request, self.template_name, self._ctx(p_form, fs))

        # Se invalidi, ripassa la mappa
        return render(request, self.template_name, self._ctx(p_form, fs))
        
class PrescrizioniListaView(LoginRequiredMixin, View):
    template_name = "core/prescrizioni_lista.html"

    def get(self, request):
        pid = request.GET.get("paziente")
        paz_qs = Paziente.objects.all().order_by("cognome", "nome")
        if pid:
            paz_qs = paz_qs.filter(pk=pid)

        presc_qs = (
            Prescrizione.objects
            .filter(paziente__in=paz_qs)
            .select_related("paziente", "medico")
            .prefetch_related("righe__farmaco", "righe__orari")
            .order_by("-attiva", "-data_inizio")
        )

        # raggruppo per paziente e preparo stringhe orari leggibili
        days_map = {"1":"Lun","2":"Mar","3":"Mer","4":"Gio","5":"Ven","6":"Sab","7":"Dom"}
        per_paz = defaultdict(list)
        for pr in presc_qs:
            righe_pack = []
            for r in pr.righe.all():
                orari_fmt = []
                for od in r.orari.all():
                    giorni = ", ".join(days_map.get(c, "") for c in od.giorni_settimana if c in days_map) or "Tutti i giorni"
                    orari_fmt.append(f"{od.ora.strftime('%H:%M')} ({giorni})")
                righe_pack.append({"r": r, "orari_fmt": orari_fmt})
            per_paz[pr.paziente_id].append({"pr": pr, "righe": righe_pack})

        data = [{"paziente": p, "entries": per_paz.get(p.id, [])} for p in paz_qs]
        ctx = {"data": data, "pazienti": Paziente.objects.all().order_by("cognome","nome"), "selected_id": pid}
        return render(request, self.template_name, ctx)

class DiarioIgieneView(LoginRequiredMixin, View):
    template_name = "core/igiene_diario.html"

    def get(self, request):
        pid = request.GET.get("paziente")
        settimana_str = request.GET.get("settimana")

        # settimana di default = quella corrente (lunedì–domenica)
        oggi = timezone.now().date()
        lun = oggi - timedelta(days=oggi.weekday())
        if settimana_str:
            try:
                lun = timezone.datetime.fromisoformat(settimana_str).date()
            except Exception:
                pass
        giorni = [lun + timedelta(days=i) for i in range(7)]

        # queryset pazienti
        if pid:
            paz_qs = Paziente.objects.filter(pk=pid)
        else:
            paz_qs = Paziente.objects.all().order_by("cognome","nome")

        # eventi di igiene della settimana
        eventi = (
            DiarioIgiene.objects
            .filter(rilevato_il__date__range=[giorni[0], giorni[-1]])
            .select_related("paziente")
        )

        # organizzo dati
        tabella = []
        for p in paz_qs:
            riga = {"paziente": p, "giorni": []}
            for g in giorni:
                ev = eventi.filter(paziente=p, rilevato_il__date=g).first()
                riga["giorni"].append(ev.get_evento_display() if ev else "")
            tabella.append(riga)

        ctx = {
            "giorni": giorni,
            "tabella": tabella,
            "pazienti": Paziente.objects.all().order_by("cognome","nome"),
            "selected_id": pid,
            "settimana": giorni[0],
        }
        return render(request, self.template_name, ctx)
        

class SomministrazioneCreateView(LoginRequiredMixin, View):
    template_name = "core/somministrazione_form.html"
    success_url = reverse_lazy("dashboard")

    def get(self, request):
        pid = request.GET.get("paziente")
        initial = {"data_ora": timezone.now()}
        if pid and Paziente.objects.filter(pk=pid).exists():
            initial["paziente"] = pid
        form = SomministrazioneForm(initial=initial, paziente_prefiltro=pid)
        pazienti = Paziente.objects.all().order_by("cognome","nome")

        righe_meta = {
            str(r.id): {
                "dose": str(r.dose_val),
                "udm": r.dose_udm,
                "forma": r.farmaco.forma or "",
            }
            for r in form.fields["riga"].queryset.select_related("farmaco")
        }

        return render(request, self.template_name, {
            "form": form,
            "pazienti": pazienti,
            "righe_meta_json": json.dumps(righe_meta),
        })

    def post(self, request):
        pid = request.POST.get("paziente") or request.GET.get("paziente")
        form = SomministrazioneForm(request.POST, paziente_prefiltro=pid)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.operatore = request.user
            obj.creato_da = request.user
            obj.aggiornato_da = request.user
            obj.save()
            messages.success(request, "Somministrazione registrata.")
            return redirect(self.success_url)
        pazienti = Paziente.objects.all().order_by("cognome","nome")
        return render(request, self.template_name, {"form": form, "pazienti": pazienti})

class DiarioSomministrazioniView(LoginRequiredMixin, View):
    template_name = "core/terapia_diario.html"

    def get(self, request):
        pid = request.GET.get("paziente")
        settimana_str = request.GET.get("settimana")

        # settimana LUN–DOM
        oggi = timezone.now().date()
        lun = oggi - timedelta(days=oggi.weekday())
        if settimana_str:
            try:
                lun = timezone.datetime.fromisoformat(settimana_str).date()
            except Exception:
                pass
        giorni = [lun + timedelta(days=i) for i in range(7)]

        # pazienti
        paz_qs = Paziente.objects.all().order_by("cognome", "nome")
        if pid:
            paz_qs = paz_qs.filter(pk=pid)

        # somministrazioni della settimana
        somms = (Somministrazione.objects
                 .filter(data_ora__date__range=[giorni[0], giorni[-1]])
                 .select_related("paziente", "riga__farmaco")
                 .order_by("data_ora"))

        # tabella: per paziente → per giorno → lista voci
        per_paz = {p.id: {g: [] for g in giorni} for p in paz_qs}
        for s in somms:
            if s.paziente_id in per_paz:
                # usa il datetime in timezone locale
                local_dt = timezone.localtime(s.data_ora)
                giorno_locale = local_dt.date()
                label = f"{local_dt:%H:%M} {s.riga.farmaco.nome} {s.dose_erogata} {s.riga.dose_udm}"
                per_paz[s.paziente_id][giorno_locale].append(label)

        tabella = []
        for p in paz_qs:
            riga = {"paziente": p, "giorni": [per_paz[p.id][g] for g in giorni]}
            tabella.append(riga)

        ctx = {
            "giorni": giorni,
            "tabella": tabella,
            "pazienti": Paziente.objects.all().order_by("cognome", "nome"),
            "selected_id": pid,
            "settimana": giorni[0],
        }
        return render(request, self.template_name, ctx)
        
class DiarioParametriView(LoginRequiredMixin, View):
    template_name = "core/parametri_diario.html"

    def get(self, request):
        pid = request.GET.get("paziente")
        giorno_str = request.GET.get("giorno")
        oggi = timezone.localdate()
        try:
            giorno = timezone.datetime.fromisoformat(giorno_str).date() if giorno_str else oggi
        except Exception:
            giorno = oggi

        pazienti = Paziente.objects.all().order_by("cognome", "nome")

        if pid:  # modalità singolo paziente
            selezionato = pazienti.filter(pk=pid).first()
            rows = (ParametroVitale.objects
                    .filter(paziente=selezionato, rilevato_il__date=giorno)
                    .select_related("operatore")
                    .order_by("rilevato_il")) if selezionato else []
            all_mode = False
        else:    # modalità "Tutti"
            selezionato = None
            rows = (ParametroVitale.objects
                    .filter(rilevato_il__date=giorno)
                    .select_related("paziente", "operatore")
                    .order_by("paziente__cognome", "paziente__nome", "rilevato_il"))
            all_mode = True

        ctx = {
            "pazienti": pazienti,
            "selected_id": pid,
            "giorno": giorno,
            "rows": rows,
            "paziente": selezionato,
            "all_mode": all_mode,
        }
        return render(request, self.template_name, ctx)
    
def paziente_anagrafica(request):
    pazienti = Paziente.objects.all().order_by("cognome", "nome")
    p_id = request.GET.get("p")

    paziente = None
    contatti = allergie = episodi = prescrizioni = documenti = []

    if p_id:
        paziente = get_object_or_404(Paziente, pk=p_id)

        contatti = paziente.contatti_emergenza.prefetch_related("recapiti").order_by("-is_primario", "cognome", "nome")
        allergie = paziente.allergie.all().order_by("-attiva", "categoria", "gravita")
        episodi = paziente.episodi.select_related("medico", "letto").all()
        prescrizioni = (
            paziente.prescrizioni
            .prefetch_related("righe", "righe__farmaco")
            .select_related("medico")
            .all()
        )
        documenti = (
            paziente.documenti
            .select_related("episodio", "caricato_da")
            .order_by("-id")
        )

    ctx = {
        "pazienti": pazienti,
        "paziente": paziente,
        "contatti": contatti,
        "allergie": allergie,
        "episodi": episodi,
        "prescrizioni": prescrizioni,
        "documenti": documenti,
    }
    return render(request, "core/paziente_anagrafica.html", ctx)

class MenuDiarioView(TemplateView):
    template_name = "core/menu_diario.html"

    def get(self, request, *args, **kwargs):
        form = MenuDiarioFilterForm(request.GET or None)
        ctx = {"form": form, "periodo": None, "weeks": []}
        if not form.is_valid():
            return self.render_to_response(ctx)

        periodo = form.cleaned_data["periodo"]
        pasto_filter = form.cleaned_data.get("pasto") or None
        giorno = form.cleaned_data.get("giorno")
        settimana_iso = form.cleaned_data.get("settimana_iso")
        q = (form.cleaned_data.get("q") or "").strip()

        # Intervallo base
        d_start, d_end = periodo.data_inizio, periodo.data_fine
        if giorno:
            d_start = d_end = giorno

        # Giorni del periodo, filtrati eventualmente per settimana ISO
        dates, d = [], d_start
        while d <= d_end:
            if not settimana_iso or d.isocalendar().week == settimana_iso:
                dates.append(d)
            d += timedelta(days=1)
        if not dates:
            ctx.update({"periodo": periodo, "weeks": []})
            return self.render_to_response(ctx)

        # Righe fisse: 4 pasti (come richiesto)
        row_order = [Pasto.COLAZ, Pasto.MEREN, Pasto.PRANZ, Pasto.CENA]
        rows = [{"code": code, "label": dict(Pasto.choices)[code]} for code in row_order]
        if pasto_filter:
            rows = [r for r in rows if r["code"] == pasto_filter]

        # Query pasti del periodo
        qp = Q(periodo=periodo, data__in=dates)
        if pasto_filter:
            qp &= Q(pasto=pasto_filter)

        voci_prefetch = Prefetch(
            "voci",
            queryset=VoceMenu.objects.select_related("pietanza").order_by("ordine", "id")
        )
        pasti = (
            MenuPasto.objects
            .filter(qp)
            .select_related("periodo")
            .prefetch_related(voci_prefetch)
            .order_by("data", "pasto")
        )

        # Ricerca testuale su voci (nome/tag/allergeni/descrizione)
        if q:
            ql = q.lower()
            def match(pm: MenuPasto):
                for v in pm.voci.all():
                    testo = (v.descrizione_libera or "")
                    if v.pietanza:
                        testo += " " + v.pietanza.nome + " " + (v.pietanza.tag_dieta or "") + " " + (v.pietanza.allergeni_note or "")
                    if ql in testo.lower():
                        return True
                return False
            pasti = [p for p in pasti if match(p)]

        # Griglia: (data, pasto_code) -> { id, items[list], note }
        grid = {}
        for p in pasti:
            items = []
            for v in p.voci.all():
                if v.pietanza:
                    label = v.pietanza.nome
                    if v.descrizione_libera:
                        label += f" – {v.descrizione_libera}"
                else:
                    label = v.descrizione_libera
                if v.note:
                    label += f" ({v.note})"
                items.append(label)
            grid[(p.data, p.pasto)] = {"id": p.id, "items": items, "note": p.note}

        # Spezza per settimane ISO
        weeks, curw, chunk = [], None, []
        for d in dates:
            w = d.isocalendar().week
            if curw is None:
                curw = w
            if w != curw:
                weeks.append({"iso_week": curw, "dates": chunk})
                curw, chunk = w, []
            chunk.append(d)
        if chunk:
            weeks.append({"iso_week": curw, "dates": chunk})

        # Per ogni settimana crea la tabella (righe pasti × colonne giorni)
        for wk in weeks:
            wk_table = []
            for r in rows:
                cells = []
                for d in wk["dates"]:
                    cell = grid.get((d, r["code"]))  # None oppure {id,items,note}
                    cells.append({"cell": cell, "date": d, "pasto_code": r["code"]})
                wk_table.append({"row": r, "cells": cells})
            wk["table"] = wk_table

        ctx.update({"form": form, "periodo": periodo, "weeks": weeks})
        return self.render_to_response(ctx)

class TurniDiarioView(TemplateView):
    template_name = "core/turni_diario.html"

    def get(self, request, *args, **kwargs):
        form = TurniDiarioFilterForm(request.GET or None)
        ctx = {"form": form, "periodo": None, "weeks": []}
        if not form.is_valid():
            return self.render_to_response(ctx)

        periodo = form.cleaned_data["periodo"]
        giorno = form.cleaned_data.get("giorno")
        settimana_iso = form.cleaned_data.get("settimana_iso")
        dip = form.cleaned_data.get("dipendente")
        ruolo = form.cleaned_data.get("ruolo") or None
        q = (form.cleaned_data.get("q") or "").strip()

        # intervallo date
        d_start, d_end = periodo.data_inizio, periodo.data_fine
        if giorno:
            d_start = d_end = giorno

        # giorni (eventuale filtro per settimana ISO)
        dates, d = [], d_start
        while d <= d_end:
            if not settimana_iso or d.isocalendar().week == settimana_iso:
                dates.append(d)
            d += timedelta(days=1)
        if not dates:
            ctx.update({"periodo": periodo, "weeks": []})
            return self.render_to_response(ctx)

        # righe = tipi turno
        turni = list(TurnoTipo.objects.all().order_by("ordine", "codice"))
        rows = [{"id": t.id, "label": t.nome or t.codice} for t in turni]

        # query assegnazioni
        qa = Q(periodo=periodo, data__in=dates)
        if dip:   qa &= Q(dipendente=dip)
        if ruolo: qa &= Q(dipendente__ruolo=ruolo)

        assegn = (
            AssegnazioneTurno.objects
            .filter(qa)
            .select_related("dipendente", "turno")
            .order_by("data","turno__ordine","dipendente__cognome","dipendente__nome")
        )

        # ricerca testuale su cognome/nome/note
        if q:
            ql = q.lower()
            assegn = [
                a for a in assegn
                if ql in f"{a.dipendente.cognome} {a.dipendente.nome} {a.note or ''}".lower()
            ]

        # griglia (data, turno_id) -> lista di item {id,cognome,nome_iniziale,note}
        grid = {}
        for a in assegn:
            nome = (a.dipendente.nome or "").strip()
            nome_iniziale = (nome[0] + ".") if nome else ""
            item = {
                "id": a.id,
                "cognome": a.dipendente.cognome,
                "nome_iniziale": nome_iniziale,
                "note": a.note or "",
            }
            key = (a.data, a.turno_id)
            grid.setdefault(key, []).append(item)

        # spezza per settimane ISO
        weeks = []
        curw, chunk = None, []
        for d in dates:
            w = d.isocalendar().week
            if curw is None:
                curw = w
            if w != curw:
                weeks.append({"iso_week": curw, "dates": chunk})
                curw, chunk = w, []
            chunk.append(d)
        if chunk:
            weeks.append({"iso_week": curw, "dates": chunk})

        # per ogni settimana crea tabella righe×colonne
        for wk in weeks:
            wk_table = []
            for r in rows:
                cells = []
                for d in wk["dates"]:
                    items = grid.get((d, r["id"]), [])
                    cells.append({"items": items, "date": d, "turno_id": r["id"]})
                wk_table.append({"row": r, "cells": cells})
            wk["table"] = wk_table

        ctx.update({"form": form, "periodo": periodo, "weeks": weeks})
        return self.render_to_response(ctx)
        
class DipendenteCreateView(CreateView):
    model = Dipendente
    form_class = DipendenteForm
    template_name = "core/dipendente_form.html"
    success_url = reverse_lazy("dashboard")  # cambia se vuoi una lista dipendenti

    def form_valid(self, form):
        resp = super().form_valid(form)
        if "save_add" in self.request.POST:
            messages.success(self.request, "Dipendente salvato. Inseriscine un altro.")
            return redirect("dipendente_nuovo")
        messages.success(self.request, "Dipendente salvato.")
        return resp

class PianoTurniPeriodoCreateView(CreateView):
    model = PianoTurniPeriodo
    form_class = PianoTurniPeriodoForm
    template_name = "core/turni_periodo_form.html"

    def get_success_url(self):
        return reverse("turni_periodo_gestisci", args=[self.object.pk])

    def form_valid(self, form):
        resp = super().form_valid(form)
        if "save_add" in self.request.POST:
            messages.success(self.request, "Periodo turni salvato. Inseriscine un altro.")
            return redirect("turni_periodo_nuovo")
        messages.success(self.request, "Periodo turni salvato. Ora gestisci i turni.")
        return resp

class TurniPeriodoGestisciView(View):
    template_name = "core/turni_periodo_gestisci.html"

    def get(self, request, pk):
        periodo = get_object_or_404(PianoTurniPeriodo, pk=pk)
        form = AssegnazioneTurnoForm(periodo=periodo)
        assegnazioni = (AssegnazioneTurno.objects
                        .filter(periodo=periodo)
                        .select_related("turno", "dipendente")
                        .order_by("data", "turno__ordine", "dipendente__cognome"))

        dipendenti = Dipendente.objects.filter(attivo=True).order_by("cognome", "nome")
        turni = TurnoTipo.objects.order_by("ordine")
        return render(request, self.template_name, {
            "periodo": periodo, "form": form, "assegnazioni": assegnazioni,
            "dipendenti": dipendenti, "turni": turni,
        })

    def post(self, request, pk):
        periodo = get_object_or_404(PianoTurniPeriodo, pk=pk)

        # --- azione: rotazione automatica ---
        if "auto_fill" in request.POST:
            return self._auto_fill(request, periodo)

        # --- azione: inserimento singolo turno ---
        form = AssegnazioneTurnoForm(request.POST, periodo=periodo)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.periodo = periodo
            obj.save()
            messages.success(request, "Turno inserito.")
            return redirect("turni_periodo_gestisci", pk=periodo.pk)

        assegnazioni = (AssegnazioneTurno.objects
                        .filter(periodo=periodo)
                        .select_related("turno", "dipendente")
                        .order_by("data", "turno__ordine", "dipendente__cognome"))
        dipendenti = Dipendente.objects.filter(attivo=True).order_by("cognome", "nome")
        turni = TurnoTipo.objects.order_by("ordine")
        return render(request, self.template_name, {
            "periodo": periodo, "form": form, "assegnazioni": assegnazioni,
            "dipendenti": dipendenti, "turni": turni,
        })

    def _auto_fill(self, request, periodo):
        # data di partenza (default = inizio periodo)
        start = parse_date(request.POST.get("start_date")) or periodo.data_inizio
        overwrite = bool(request.POST.get("overwrite"))

        turni = list(TurnoTipo.objects.order_by("ordine"))
        n = len(turni)  # es. 4: Mattina, Pomeriggio, Notte, Riposo

        # dipendenti scelti nell'ordine del giorno iniziale (Mattina..Riposo)
        dip_ids = [request.POST.get(f"op{i}") for i in range(1, n + 1)]
        dips = [Dipendente.objects.get(pk=pk) for pk in dip_ids if pk]

        if len(dips) != n:
            messages.error(request, "Seleziona un dipendente per ogni turno del giorno iniziale.")
            return redirect("turni_periodo_gestisci", pk=periodo.pk)

        created, updated, skipped = 0, 0, 0
        day = start
        while day <= periodo.data_fine:
            day_offset = (day - start).days  # 0,1,2,...
            # mappatura: indice turno i → dipendente dips[(i - day_offset) % n]
            for i, turno in enumerate(turni):
                dip = dips[(i - day_offset) % n]

                # gestisci eventuali collisioni
                qs = AssegnazioneTurno.objects.filter(periodo=periodo, data=day, dipendente=dip)
                if qs.exists():
                    if not overwrite:
                        skipped += 1
                        continue
                    qs.delete()

                obj, created_flag = AssegnazioneTurno.objects.get_or_create(
                    periodo=periodo, data=day, dipendente=dip,
                    defaults={"turno": turno}
                )
                if created_flag:
                    created += 1
                else:
                    if obj.turno_id != turno.id:
                        obj.turno = turno
                        obj.save(update_fields=["turno"])
                        updated += 1
            day += timedelta(days=1)

        messages.success(
            request,
            f"Rotazione completata: {created} nuove, {updated} aggiornate, {skipped} saltate."
        )
        return redirect("turni_periodo_gestisci", pk=periodo.pk)
        
class TurniPeriodoSelezionaView(View):
    template_name = "core/turni_periodo_seleziona.html"

    def get(self, request):
        periodi = PianoTurniPeriodo.objects.order_by("-data_inizio")
        selected = periodi.first().pk if periodi else None
        return render(request, self.template_name, {"periodi": periodi, "selected": selected})

    def post(self, request):
        pk = request.POST.get("periodo_id")
        if not pk:
            messages.error(request, "Seleziona un periodo.")
            return redirect("turni_periodo_seleziona")
        return redirect("turni_periodo_gestisci", pk=pk)

class MenuPeriodoCreateView(CreateView):
    model = MenuPeriodo
    form_class = MenuPeriodoForm
    template_name = "core/menu_periodo_form.html"

    def get_success_url(self):
        # Dopo "Salva" ti porto al diario menu (già presente nelle tue URL)
        return reverse("menu_diario")  # puoi cambiare in futuro a "gestisci periodo menu"

    def form_valid(self, form):
        resp = super().form_valid(form)
        if "save_add" in self.request.POST:
            messages.success(self.request, "Periodo menu salvato. Inseriscine un altro.")
            return redirect("menu_periodo_nuovo")  # <<< invece di reverse_lazy(...)
        messages.success(self.request, "Periodo menu salvato.")
        return resp
        
class PietanzaCreateView(CreateView):
    model = Pietanza
    form_class = PietanzaForm
    template_name = "core/pietanza_form.html"

    def get_success_url(self):
        return reverse("menu_diario")  # pagina già presente
    # Se preferisci restare sul form, usa: return reverse("pietanza_nuova")

    def form_valid(self, form):
        resp = super().form_valid(form)  # salva e prepara redirect di default
        if "save_add" in self.request.POST:
            from django.contrib import messages
            messages.success(self.request, "Pietanza salvata. Inseriscine un'altra.")
            return redirect("pietanza_nuova")  # <<< HttpResponseRedirect corretto
        messages.success(self.request, "Pietanza salvata.")
        
def build_menu_weeks(periodo, pasto_filter=None):
    # intervallo date (tutto il periodo)
    d_start, d_end = periodo.data_inizio, periodo.data_fine

    dates, d = [], d_start
    while d <= d_end:
        dates.append(d)
        d += timedelta(days=1)
    if not dates:
        return []

    # righe fisse
    row_order = [Pasto.COLAZ, Pasto.MEREN, Pasto.PRANZ, Pasto.CENA]
    rows = [{"code": code, "label": dict(Pasto.choices)[code]} for code in row_order]
    if pasto_filter:
        rows = [r for r in rows if r["code"] == pasto_filter]

    # query pasti
    qp = Q(periodo=periodo, data__in=dates)
    if pasto_filter:
        qp &= Q(pasto=pasto_filter)

    voci_prefetch = Prefetch(
        "voci",
        queryset=VoceMenu.objects.select_related("pietanza").order_by("ordine", "id")
    )
    pasti = (
        MenuPasto.objects
        .filter(qp)
        .select_related("periodo")
        .prefetch_related(voci_prefetch)
        .order_by("data", "pasto")
    )

    # griglia (data, pasto_code) -> cella
    grid = {}
    for p in pasti:
        items = []
        for v in p.voci.all():
            if v.pietanza:
                label = v.pietanza.nome
                if v.descrizione_libera:
                    label += f" – {v.descrizione_libera}"
            else:
                label = v.descrizione_libera
            if v.note:
                label += f" ({v.note})"
            items.append(label)
        grid[(p.data, p.pasto)] = {"id": p.id, "items": items, "note": p.note}

    # spezza in settimane ISO
    weeks, curw, chunk = [], None, []
    for d in dates:
        w = d.isocalendar().week
        if curw is None:
            curw = w
        if w != curw:
            weeks.append({"iso_week": curw, "dates": chunk})
            curw, chunk = w, []
        chunk.append(d)
    if chunk:
        weeks.append({"iso_week": curw, "dates": chunk})

    # tabella per ciascuna settimana
    for wk in weeks:
        wk_table = []
        for r in rows:
            cells = []
            for d in wk["dates"]:
                cell = grid.get((d, r["code"]))  # None oppure {id,items,note}
                cells.append({"cell": cell, "date": d, "pasto_code": r["code"]})
            wk_table.append({"row": r, "cells": cells})
        wk["table"] = wk_table

    return weeks

class ReportMenuPeriodoSelectView(FormView):
    template_name = "core/report_menu_periodo_select.html"
    form_class = MenuPeriodoSelectForm

    def form_valid(self, form):
        return redirect("report_menu_periodo_print", pk=form.cleaned_data["periodo"].pk)

class ReportMenuPeriodoPrintView(View):
    template_name = "core/report_menu_periodo_print.html"

    def get(self, request, pk):
        periodo = get_object_or_404(MenuPeriodo, pk=pk)
        weeks = build_menu_weeks(periodo)
        ctx = {"periodo": periodo, "weeks": weeks}
        return render(request, self.template_name, ctx)