#!/usr/bin/env python3
"""
Script de Verificación y Prueba de Carga para Autoescalado Horizontal (HPA).
Proyecto: k8s-recreate-deployment (Plataformas II)
Autores: Esteban Guarín Valencia, Juan José Arias Gallego
"""

import sys
import time
import argparse
import threading
import urllib.request
import urllib.error
from datetime import datetime


stop_workers = False
success_counter = 0
error_counter = 0


def worker_load_generator(target_url: str, cpu_seconds: float, host_header: str = "recreate.local"):
    global success_counter, error_counter, stop_workers
    endpoint = f"{target_url.rstrip('/')}/simulate/cpu-load?seconds={cpu_seconds}"

    while not stop_workers:
        try:
            req = urllib.request.Request(
                endpoint,
                headers={
                    "User-Agent": "HPA-Load-Tester/1.0",
                    "Host": host_header or "recreate.local",
                },
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                if resp.status == 200:
                    success_counter += 1
                else:
                    error_counter += 1
        except Exception:
            error_counter += 1
        time.sleep(0.05)


def run_hpa_stress_test(target_url: str, concurrency: int, duration: int, cpu_duration: float, host_header: str = "recreate.local"):
    global stop_workers, success_counter, error_counter
    print("=" * 70)
    print("PRUEBA DE ESTRÉS Y VALIDACIÓN DE AUTOESCALADO (HPA)")
    print(f"URL Objetivo: {target_url} (Host: {host_header})")
    print(f"Hilos Concurrentes: {concurrency}")
    print(f"Duración de la Carga: {duration} segundos")
    print(f"Carga de CPU por solicitud: {cpu_duration} segundos")
    print("=" * 70)

    print("\nIniciando hilos de generación de carga para saturar CPU de los Pods...")
    threads = []
    for _ in range(concurrency):
        t = threading.Thread(target=worker_load_generator, args=(target_url, cpu_duration, host_header), daemon=True)
        t.start()
        threads.append(t)

    start_time = time.time()
    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
            remaining = duration - elapsed
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"[{current_time}] Carga activa ({elapsed:.0f}s / {duration}s) | "
                  f"Peticiones completadas: {success_counter} | Errores: {error_counter} | "
                  f"Tiempo restante: {remaining:.0f}s")
            print("  -> Sugerencia: En otra terminal ejecute: kubectl get hpa -n recreate-lab -w")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nPrueba de estrés interrumpida manualmente.")

    stop_workers = True
    print("\nDeteniendo generadores de carga...")
    for t in threads:
        t.join(timeout=1.0)

    total_time = time.time() - start_time
    print("=" * 70)
    print("RESUMEN DE PRUEBA HPA")
    print(f"Duración de prueba: {total_time:.2f} segundos")
    print(f"Solicitudes exitosas: {success_counter}")
    print(f"Solicitudes fallidas: {error_counter}")
    print(f"Tasa promedio: {success_counter/max(1, total_time):.1f} req/s")
    print("Fase de enfriamiento (Scale Down):")
    print("Observe durante los próximos 60 segundos cómo Kubernetes estabiliza y reduce las réplicas:")
    print("  kubectl get pods -n recreate-lab")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prueba de Carga para HPA en Kubernetes")
    parser.add_argument("--url", default="http://recreate.local", help="URL base del Ingress o servicio")
    parser.add_argument("--concurrency", type=int, default=15, help="Número de clientes concurrentes (default: 15)")
    parser.add_argument("--duration", type=int, default=60, help="Duración en segundos (default: 60)")
    parser.add_argument("--cpu-load", type=float, default=0.5, help="Segundos de cálculo por petición (default: 0.5)")
    parser.add_argument("--host", default="recreate.local", help="Cabecera Host HTTP para Ingress (default: recreate.local)")
    args = parser.parse_args()

    run_hpa_stress_test(target_url=args.url, concurrency=args.concurrency, duration=args.duration, cpu_duration=args.cpu_load, host_header=args.host)

