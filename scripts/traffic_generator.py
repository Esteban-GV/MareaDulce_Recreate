#!/usr/bin/env python3
"""
Generador de Tráfico Continuo y Medidor de Indisponibilidad (Downtime).
Proyecto: Marea Dulce (Kubernetes Recreate Stack)
Autores: Esteban Guarín Valencia, Juan José Arias Gallego
"""

import sys
import time
import socket
import subprocess
import argparse
import urllib.request
import urllib.error
import json
from datetime import datetime


def resolve_target_url(target_url: str, host_header: str) -> tuple[str, str]:
    clean_url = target_url.rstrip("/")
    if not clean_url.endswith("/api/v1/version") and not clean_url.endswith("/healthz"):
        clean_url = f"{clean_url}/api/v1/version"

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


def run_traffic_test(target_url: str, interval: float, duration: int, host_header: str = "recreate.local"):
    resolved_url, effective_host = resolve_target_url(target_url, host_header)
    print("=" * 70)
    print("MAREA DULCE: MEDIDOR DE DOWNTIME Y TELEMETRÍA K8S RECREATE")
    print(f"URL Objetivo: {target_url} -> {resolved_url} (Host: {effective_host})")
    print(f"Intervalo: {interval}s ({1.0/interval:.1f} req/s)")
    print(f"Duración máxima: {duration if duration > 0 else 'Indefinida'} segundos")
    print("=" * 70)

    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    status_counts = {}

    downtime_start = None
    downtime_periods = []
    current_version = None

    start_timestamp = time.time()

    try:
        while True:
            elapsed = time.time() - start_timestamp
            if duration > 0 and elapsed >= duration:
                break

            total_requests += 1
            req_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            is_success = False
            status_code = None
            error_msg = ""

            try:
                req = urllib.request.Request(
                    resolved_url,
                    headers={
                        "User-Agent": "Marea-Traffic-Generator/1.0",
                        "Host": effective_host,
                    },
                )
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    status_code = resp.status
                    is_success = 200 <= status_code < 400
                    raw_data = resp.read().decode("utf-8")
                    try:
                        data = json.loads(raw_data)
                        if "version" in data:
                            current_version = data["version"]
                    except Exception:
                        pass
            except urllib.error.HTTPError as e:
                status_code = e.code
                error_msg = f"HTTP {e.code}"
            except urllib.error.URLError as e:
                status_code = 0
                error_msg = f"Conexión rechazada / timeout ({e.reason})"
            except Exception as e:
                status_code = -1
                error_msg = str(e)

            status_label = str(status_code) if status_code else "ERROR_RED"
            status_counts[status_label] = status_counts.get(status_label, 0) + 1

            if is_success:
                successful_requests += 1
                if downtime_start is not None:
                    dt_duration = time.time() - downtime_start
                    downtime_periods.append(dt_duration)
                    print(f"\n[RESTABLECIMIENTO] Servicio recuperado a las {req_time}. "
                          f"Downtime registrado: {dt_duration:.3f} segundos.\n")
                    downtime_start = None
                print(f"[{req_time}] REQ #{total_requests:04d} -> HTTP {status_code} "
                      f"(Versión activa: {current_version or 'N/A'})")
            else:
                failed_requests += 1
                if downtime_start is None:
                    downtime_start = time.time()
                    print(f"\n[ALERTA DOWNTIME] Interrupción de servicio detectada a las {req_time}: {error_msg}")
                print(f"[{req_time}] REQ #{total_requests:04d} -> FALLO: {error_msg}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nPrueba interrumpida manualmente por el usuario.")

    # Resumen final
    total_time = time.time() - start_timestamp
    print("\n" + "=" * 70)
    print("RESUMEN DE TELEMETRÍA Y OBSERVABILIDAD")
    print(f"Tiempo total evaluado: {total_time:.2f} segundos")
    print(f"Total de solicitudes enviadas: {total_requests}")
    print(f"Solicitudes exitosas: {successful_requests} ({successful_requests/max(1, total_requests)*100:.1f}%)")
    print(f"Solicitudes fallidas: {failed_requests} ({failed_requests/max(1, total_requests)*100:.1f}%)")
    print("Distribución de códigos de respuesta:")
    for code, count in sorted(status_counts.items()):
        print(f"  - {code}: {count} peticiones")

    if downtime_periods:
        total_dt = sum(downtime_periods)
        print(f"Tiempo de Indisponibilidad Total (Downtime medido): {total_dt:.3f} segundos")
        print(f"Promedio por corte: {total_dt/len(downtime_periods):.3f} segundos")
    elif downtime_start is not None:
        dt_duration = time.time() - downtime_start
        print(f"El servicio terminó en estado caído. Downtime acumulado: {dt_duration:.3f} segundos")
    else:
        print("No se registraron interrupciones en el servicio durante la prueba.")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Medidor de Downtime para Kubernetes Recreate")
    parser.add_argument("--url", default="http://localhost:8080", help="URL objetivo del servicio o Ingress (default: http://localhost:8080)")
    parser.add_argument("--interval", type=float, default=0.2, help="Intervalo en segundos entre solicitudes (default: 0.2s = 5 req/s)")
    parser.add_argument("--duration", type=int, default=0, help="Duración máxima en segundos (0 para infinito)")
    parser.add_argument("--host", default="recreate.local", help="Cabecera Host HTTP para el Ingress (default: recreate.local)")
    args = parser.parse_args()

    run_traffic_test(target_url=args.url, interval=args.interval, duration=args.duration, host_header=args.host)
