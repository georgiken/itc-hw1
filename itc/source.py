"""Задача 1.1: описание дискретного источника, валидация, генерация."""
import json
import random
from fractions import Fraction
from math import lcm

from .errors import InputError
from .probs import parse_dist, Sampler


class Model:
    """Модель символа. order = 0 — без памяти; order = d — марковская глубины d.
    table: контекст (кортеж последних символов длины <= order) -> распределение."""

    def __init__(self, name, order, table):
        self.name, self.order, self.table = name, order, table

    def cond(self, history):
        ctx = tuple(history[len(history) - min(len(history), self.order):]) if self.order else ()
        return self.table[ctx]

    def alphabet(self):
        return {s for d in self.table.values() for s in d}


class Component:
    """Источник исходного формата: модели, переключатели, циклический список source."""

    def __init__(self, models, switches, source):
        self.models, self.switches, self.source = models, switches, source
        self.L = len(source)
        self.order = max(m.order for m in models.values())

    def tick_dist(self, t, history):
        """Распределение символа на такте t (с нуля) при данной предыстории."""
        sw = self.switches[self.source[t % self.L]]
        out = {}
        for mname, pm in sw.items():
            if pm == 0:
                continue
            for sym, ps in self.models[mname].cond(history).items():
                out[sym] = out.get(sym, Fraction(0)) + pm * ps
        return out


class Source:
    """Смесь компонент с весами; исходный формат — одна компонента с весом 1."""

    def __init__(self, components):
        self.components = components  # список (вес, Component)
        self.alphabet = sorted(set().union(*(m.alphabet() for _, c in components
                                             for m in c.models.values())))

    @property
    def period(self):
        return lcm(*(c.L for _, c in self.components))

    # ---------- точные вероятности ----------
    @staticmethod
    def _comp_prob_at(comp, seq, j):
        """Pr{X_{j+1} = a_1, ..., X_{j+r} = a_r} для одной компоненты.
        Прямой проход по состояниям «последние order символов»: для источника
        без памяти состояние одно (пустое) и проход вырождается в произведение."""
        d = comp.order
        states = {(): Fraction(1)}
        for t in range(j):  # маргинализуем символы до позиции j
            if d == 0:
                break
            nxt = {}
            for h, p in states.items():
                for sym, ps in comp.tick_dist(t, h).items():
                    nh = (h + (sym,))[-d:]
                    nxt[nh] = nxt.get(nh, Fraction(0)) + p * ps
            states = nxt
        total = Fraction(0)
        for h, p in states.items():
            for i, a in enumerate(seq):
                if p == 0:
                    break
                p *= comp.tick_dist(j + i, h).get(a, Fraction(0))
                if d:
                    h = (h + (a,))[-d:]
            total += p
        return total

    def prob_at(self, seq, j=0):
        return sum((w * self._comp_prob_at(c, seq, j) for w, c in self.components), Fraction(0))

    def prob_period_avg(self, seq):
        P = self.period
        return sum((self.prob_at(seq, j) for j in range(P)), Fraction(0)) / P

    # ---------- генерация ----------
    def generate(self, rng):
        """Бесконечный генератор символов одной реализации."""
        comp_sampler = Sampler({i: w for i, (w, _) in enumerate(self.components)})
        comp = self.components[comp_sampler.draw(rng)][1]  # выбор компоненты — один раз
        cache = {}
        history = []
        t = 0
        while True:
            ctx = tuple(history[-comp.order:]) if comp.order else ()
            key = (t % comp.L, ctx if len(history) >= comp.order else ("<", ctx))
            s = cache.get(key)
            if s is None:
                s = cache[key] = Sampler(comp.tick_dist(t, history))
            sym = s.draw(rng)
            yield sym
            if comp.order:
                history.append(sym)
                if len(history) > comp.order:
                    del history[0]
            t += 1

    def joiner(self):
        return "" if all(len(s) == 1 for s in self.alphabet) else " "


# ---------- разбор ----------
def _parse_models(obj):
    if not isinstance(obj, dict) or not obj:
        raise InputError("models: ожидается непустой объект")
    return {name: Model(name, 0, {(): parse_dist(d, f"models[{name!r}]")})
            for name, d in obj.items()}


def _parse_component(obj, where="источник"):
    if not isinstance(obj, dict):
        raise InputError(f"{where}: ожидается JSON-объект")
    for key in ("models", "switches", "source"):
        if key not in obj:
            raise InputError(f"{where}: нет поля {key!r}")
    models = _parse_models(obj["models"])
    sw_obj = obj["switches"]
    if not isinstance(sw_obj, dict) or not sw_obj:
        raise InputError(f"{where}: switches — ожидается непустой объект")
    switches = {}
    for sname, d in sw_obj.items():
        dist = parse_dist(d, f"switches[{sname!r}]")
        for m in dist:
            if m not in models:
                raise InputError(f"switches[{sname!r}]: несуществующая модель {m!r}")
        switches[sname] = dist
    src = obj["source"]
    if not isinstance(src, list):
        raise InputError(f"{where}: source должен быть списком")
    if not src:
        raise InputError(f"{where}: пустой список source")
    for s in src:
        if not isinstance(s, str) or s not in switches:
            raise InputError(f"source: несуществующий переключатель {s!r}")
    return Component(models, switches, list(src))


def parse_source(obj) -> Source:
    return Source([(Fraction(1), _parse_component(obj))])


def load_source(path) -> Source:
    try:
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
    except FileNotFoundError:
        raise InputError(f"файл не найден: {path}") from None
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise InputError(f"{path}: некорректный JSON ({e})") from None
    except OSError as e:
        raise InputError(f"{path}: {e.strerror}") from None
    return parse_source(obj)


def make_rng(seed):
    return random.Random(seed)
