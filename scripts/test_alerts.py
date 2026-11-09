#!/usr/bin/env python3
"""
Script de Disparo y Validación de Alarmas de Observabilidad.
Proyecto: k8s-recreate-deployment (Plataformas II)
Autores: Esteban Guarín Valencia, Juan José Arias Gallego
"""

import sys
import time
import socket
import subprocess
import argparse
import urllib.request
import urllib.error
from datetime import datetime


def resolve_base_url(target_url: str, host_header: str) -> tuple[str, str]:
    clean_url = target_url.rstrip("/")
    if "://recreate.local" in clean_url:
        try:
            socket.gethostbyname("recreate.local")
        except socket.gaierror:
            ingress_ip = "192.168.49.2"
            try:
                out = subprocess.check_output(
                    ["kubectl", "get", "ingress", "-n", "recreate-lab", "-o", "jsonpath={.items[0].status.loadBalancer.ingress[0].ip}"],
                    text=True,
                    timeout=3,
                ).strip()
                if out:
                    ingress_ip = out
            except Exception:
                pass
            clean_url = clean_url.replace("://recreate.local", f"://{ingress_ip}")
            host_header = "recreate.local"
    return clean_url, (host_header or "recreate.local")


def trigger_error_rate_alarm(target_url: str, request_count: int, host_header: str = "recreate.local"):
    print("\n--- 1. PROBANDO ALARMA: TASA ELEVADA DE ERRORES HTTP (5xx) ---")
    print(f"Enviando {request_count} peticiones con código HTTP 500 para elevar la tasa de error...")
    endpoint = f"{target_url.rstrip('/')}/simulate/error?status_code=500"

    errors_triggered = 0
    for i in range(1, request_count + 1):
        try:
            req = urllib.request.Request(
                endpoint,
                headers={
                    "User-Agent": "Alert-Tester/1.0",
                    "Host": host_header or "recreate.local",
                },
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                pass
        except urllib.error.HTTPError as e:
            if e.code == 500:
                errors_triggered += 1
        except Exception:
            errors_triggered += 1

        if i % 10 == 0 or i == request_count:
            print(f"  Progreso: {i}/{request_count} errores 500 generados...")
        time.sleep(0.05)

    print(f"Resultado: {errors_triggered} errores forzados.")
    print("Verifique en Grafana / Prometheus Alertmanager la activación de la alerta 'HighHttp5xxErrorRate'.")


def trigger_latency_alarm(target_url: str, request_count: int, delay_seconds: float, host_header: str = "recreate.local"):
    print(f"\n--- 2. PROBANDO ALARMA: LATENCIA ELEVADA (>1s) ---")
    print(f"Enviando {request_count} solicitudes lentas (demora forzada: {delay_seconds}s)...")
    endpoint = f"{target_url.rstrip('/')}/simulate/latency?delay={delay_seconds}"

    for i in range(1, request_count + 1):
        start = time.time()
        try:
            req = urllib.request.Request(
                endpoint,
                headers={
                    "User-Agent": "Alert-Tester/1.0",
                    "Host": host_header or "recreate.local",
                },
            )
            with urllib.request.urlopen(req, timeout=delay_seconds + 3.0) as resp:
                dur = time.time() - start
                print(f"  Petición #{i}: Latencia registrada = {dur:.2f}s")
        except Exception as e:
            print(f"  Petición #{i}: Error -> {e}")
        time.sleep(0.1)

    print("Verifique en Grafana / Prometheus Alertmanager la activación de la alerta 'HighRequestLatencyP95'.")


def main():
    parser = argparse.ArgumentParser(description="Disparador de Alarmas para Observabilidad en Kubernetes")
    parser.add_argument("--url", default="http://recreate.local", help="URL base del Ingress o servicio")
    parser.add_argument("--type", choices=["errors", "latency", "all"], default="all", help="Tipo de alarma a probar")
    parser.add_argument("--errors-count", type=int, default=40, help="Cantidad de peticiones con error a disparar")
    parser.add_argument("--latency-count", type=int, default=8, help="Cantidad de peticiones con latencia a disparar")
    parser.add_argument("--latency-delay", type=float, default=1.5, help="Retardo en segundos por petición lenta")
    parser.add_argument("--host", default="recreate.local", help="Cabecera Host HTTP para Ingress (default: recreate.local)")
    args = parser.parse_args()

    resolved_url, effective_host = resolve_base_url(args.url, args.host)

    print("=" * 70)
    print("DISPARADOR DE ALARMAS DE OBSERVABILIDAD")
    print(f"URL Objetivo: {args.url} -> {resolved_url} (Host: {effective_host})")
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if args.type in ["errors", "all"]:
        trigger_error_rate_alarm(resolved_url, args.errors_count, host_header=effective_host)

    if args.type in ["latency", "all"]:
        trigger_latency_alarm(resolved_url, args.latency_count, args.latency_delay, host_header=effective_host)

    print("\n" + "=" * 70)
    print("PRUEBA DE ALARMAS CONCLUIDA")
    print("Verifique en Prometheus UI (Alerts tab) o Grafana Dashboards la transición:")
    print("  Inactive -> Pending -> Firing")
    print("=" * 70)


if __name__ == "__main__":
    main()

