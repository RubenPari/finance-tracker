from __future__ import annotations

import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from apps.transactions.models import Transaction


def _extract_services_from_md(md_text: str) -> set[str]:
    services: set[str] = set()
    # Table row: | Service | ...
    for line in md_text.splitlines():
        line = line.strip()
        if not (line.startswith('|') and line.endswith('|')):
            continue
        cols = [c.strip() for c in line.strip('|').split('|')]
        if not cols:
            continue
        head = cols[0]
        if head.lower() in {'servizio', 'categoria', '---', '**subtotale**', '**totale complessivo**'}:
            continue
        if head.startswith('**') and head.endswith('**'):
            head = head.strip('*').strip()
        # skip separator row like |---|---|
        if re.fullmatch(r'-{3,}', head):
            continue
        services.add(head)
    # Remove obvious non-services
    services.discard('**Subtotale**')
    return services


def _normalize_label(s: str) -> str:
    s = s.casefold()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


class Command(BaseCommand):
    help = "Compare detected recurring merchants against a manual markdown report."

    def add_arguments(self, parser):
        parser.add_argument(
            '--md',
            default='abbonamenti_2026.md',
            help='Path to manual markdown report (default: abbonamenti_2026.md)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='User id to analyze (required)',
        )
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Lookback months (default: 12)',
        )

    def handle(self, *args, **options):
        md_path = Path(options['md'])
        if not md_path.exists():
            raise SystemExit(f'Markdown file not found: {md_path}')

        manual_text = md_path.read_text(encoding='utf-8')
        manual = {_normalize_label(x) for x in _extract_services_from_md(manual_text)}

        now = timezone.now()
        lookback_start = now - relativedelta(months=int(options['months']))

        txs = Transaction.objects.filter(
            user_id=int(options['user_id']),
            amount__lt=0,
            completed_at__gte=lookback_start,
        ).values_list('description', flat=True)
        # naive baseline: unique merchant strings normalized
        detected = {_normalize_label(d) for d in txs if d}

        # Compute overlap using containment heuristics (manual label appears in some detected labels)
        matched = set()
        for m in manual:
            if any(m in d for d in detected):
                matched.add(m)

        missing = sorted(manual - matched)
        false_pos = sorted([d for d in detected if not any(m in d for m in manual)])

        self.stdout.write(self.style.SUCCESS('Manual services count: %d' % len(manual)))
        self.stdout.write(self.style.SUCCESS('Detected labels count: %d' % len(detected)))
        self.stdout.write(self.style.SUCCESS('Matched (heuristic) count: %d' % len(matched)))
        if manual:
            recall = len(matched) / len(manual)
            self.stdout.write(self.style.SUCCESS('Recall (heuristic): %.3f' % recall))

        self.stdout.write('\nMissing (manual but not detected):')
        for m in missing[:80]:
            self.stdout.write(f'  - {m}')

        self.stdout.write('\nPotential false positives (detected but not in manual) - sample:')
        for d in false_pos[:80]:
            self.stdout.write(f'  - {d}')

