"""
run.py — Script para probar detección directamente sin servidor web
Uso: python run.py
"""
from camera import get_frame
from detector import detect_species
from logger import save_log, print_last_log


def main():
    print("🌿 Species Detector — Prueba rápida")
    print("-" * 40)

    try:
        print("📷 Capturando frame de cámara...")
        frame = get_frame()

        print("🔬 Detectando especies...")
        species = detect_species(frame)

        if species:
            print(f"\n✅ {len(species)} especies detectadas:")
            for s in species:
                print(f"   🌿 {s['class']} — {s['confidence_pct']}")
        else:
            print("⚠️  No se detectaron especies en el frame")

        save_log(species)
        print("\n📋 Historial:")
        print_last_log()

    except RuntimeError as e:
        print(f"❌ Error de cámara: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()









