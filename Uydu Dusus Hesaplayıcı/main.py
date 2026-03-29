import sys
from rich.console import Console
from rich.table import Table
from hermes_core.agent import HermesAgent
from data.mission_debris_ledger import DebrisLedger
from hermes_db.impact_engine import HermesDB

console = Console()

def print_header():
    console.print("[bold cyan]=================================================[/bold cyan]")
    console.print("[bold yellow] H.E.R.M.E.S.[/bold yellow] - Space Debris Mitigation & Post-Mission Auditor AI")
    console.print("[bold cyan]=================================================[/bold cyan]")
    console.print("[dim]Target: ZERO NET DEBRIS | Enforcing Orbital Compliance[/dim]\n")

def simulate_mission(agent):
    console.print("\n[bold magenta]>> SIMULATING FLIGHT: ASTROSAT-9 rideshare[/bold magenta]\n")
    
    # Mock mission elements based on HERMES compliance framework
    elements = [
        {
            "id": "SAT-PRIMARY-9",
            "category": "CATEGORY B",
            "mass_kg": 1500,
            "strategy": "GRAVEYARD", # HC-003 constraint check & SC-005 check
            "orbit": {"type": "GEO"},
            "metrics": {
                "cd_area": 5.0, "controlled_reentry": False, "passivation_plan": "COMPLETE", 
                "regulatory_compliant": True, "congestion_index": 0.8,
                "graveyard_fuel_margin": 1.2, # Violates HC-003 (needs 1.4)
                "fuel_reserve_pct": 2.0 # Violates SC-005 (needs 5.0)
            }
        },
        {
            "id": "UPPER-STAGE-B2",
            "category": "CATEGORY A",
            "mass_kg": 3200,
            "strategy": "REENTRY", # HC-004 & SC-002 check
            "orbit": {"type": "LEO"},
            "metrics": {
                "cd_area": 12.0, "controlled_reentry": False, "passivation_plan": "PARTIAL", # Violates HC-005
                "regulatory_compliant": False, "congestion_index": 0.5,
                "delta_v_cost_ratio": 0.10, # Triggers SC-002 (Advisory)
                "deorbit_timeline_years": 8.0 # Violates HC-002
            }
        },
        {
            "id": "NOSE-FAIRING",
            "category": "CATEGORY A",
            "mass_kg": 800,
            "strategy": "UNDEFINED", # HC-001 constraint check (Blocking)
            "orbit": {"type": "LEO"},
            "metrics": {
                "cd_area": 8.0, "controlled_reentry": False, "passivation_plan": "NONE", 
                "regulatory_compliant": False, "congestion_index": 0.9,
                "has_active_avoidance": False # Violates HC-006 (dense orbit >0.8, area>0.1)
            }
        }
    ]
    
    # Run evaluation
    agent.evaluate_mission("MSN-ASTRO-09", elements)
    
    # Display table for elements
    table = Table(title="MISSION DEBRIS SCORE (MDS) COMPONENT TRACKER", show_header=True, header_style="bold magenta")
    table.add_column("Element ID", justify="left", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Disposal Strategy", justify="center", style="green")
    table.add_column("Mass (kg)", justify="right", style="green")

    for el in elements:
        table.add_row(el["id"], el["category"], el["strategy"], str(el["mass_kg"]))

    console.print()
    console.print(table)
    console.print()
    

def fetch_ledger():
    ledger = DebrisLedger()
    # Assuming MSN-ASTRO-09 was just simulated
    elements = ledger.fetch_mission_elements("MSN-ASTRO-09")
    if not elements:
        console.print("[yellow]No elements found in ledger for MSN-ASTRO-09. Run simulation first.[/yellow]")
        return
        
    table = Table(title="DEBRIS LEDGER - MSN-ASTRO-09", show_header=True, header_style="bold cyan")
    table.add_column("Element ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Updated", style="dim")
    
    for el in elements:
        table.add_row(el['id'], el['status'], el['last_updated'])
        
    console.print(table)


def query_hermes_db():
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="hermes_spaceport_ai")
    
    console.print("\n[bold cyan]--- HERMES-DB: HISTORICAL DEBRIS QUERY ---[/bold cyan]")
    rocket = input("Enter Rocket Model (e.g., Saturn V, Falcon 9, Long March 5B, Proton-M): ").strip()
    location_input = input("Enter Launch Site (e.g., 'Istanbul' OR '28.5, -80.5'): ").strip()
    azimuth_str = input("Enter Mission Launch Azimuth (deg, e.g. 90 for East): ").strip()
    
    lat, lon = 28.5, -80.5
    site_name = location_input if location_input else "Kennedy Space Center"
    
    if location_input:
        if "," in location_input and location_input.split(",")[0].strip().replace(".","").replace("-","").isnumeric():
            # Koordinat (lat, lon) kontrolü
            parts = location_input.split(",")
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                site_name = "Custom Coordinates"
            except: pass
        else:
            # Geopy Şehir sorgusu
            console.print(f"[dim]Searching coordinates for '{location_input}'...[/dim]")
            try:
                location = geolocator.geocode(location_input)
                if location:
                    lat, lon = location.latitude, location.longitude
                    site_name = location.address.split(",")[0]
                    console.print(f"[green]Found: {site_name} ({lat:.4f}, {lon:.4f})[/green]")
                else:
                    console.print(f"[red]Could not find '{location_input}'. Using defaults.[/red]")
            except Exception as e:
                console.print(f"[red]Geocoding error. Using defaults.[/red]")
                
    try:
        azimuth = float(azimuth_str) if azimuth_str else 90.0
    except ValueError:
        azimuth = 90.0

    query = {
        "launch_site": {"name": site_name, "latitude": lat, "longitude": lon},
        "rocket_model": rocket,
        "mission_profile": {"azimuth_deg": azimuth}
    }
    
    db = HermesDB()
    report = db.generate_impact_report(query)
    console.print("\n" + report + "\n")

def train_ai():
    """Fizik motorundan veri üretip sinir ağını eğitir."""
    import numpy as np
    from hermes_db.physics_engine import generate_training_data
    from hermes_db.trajectory_ai import TrajectoryAI, MODEL_PATH

    console.print("\n[bold cyan]══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold yellow]HERMES TRAJECTORY AI - EĞİTİM MODU[/bold yellow]")
    console.print("[bold cyan]══════════════════════════════════════════════════════════[/bold cyan]")

    samples_str = input("Kaç simülasyon üretilsin? (varsayılan: 3000): ").strip()
    epochs_str = input("Kaç epoch eğitim? (varsayılan: 2000): ").strip()
    num_samples = int(samples_str) if samples_str else 3000
    num_epochs = int(epochs_str) if epochs_str else 2000

    console.print(f"\n[dim]Fizik motoru ile {num_samples} rastgele roket simüle ediliyor...[/dim]")
    X, y = generate_training_data(num_samples=num_samples, verbose=True)
    console.print(f"[green]✓ {X.shape[0]} geçerli eğitim örneği üretildi.[/green]")

    if X.shape[0] < 50:
        console.print("[red]Yetersiz veri. Daha fazla örnek deneyin.[/red]")
        return

    console.print(f"\n[dim]Sinir ağı eğitiliyor ({num_epochs} epoch)...[/dim]")
    model = TrajectoryAI()
    model.train(X, y, epochs=num_epochs, lr=0.001, batch_size=64,
                verbose_fn=lambda msg: console.print(f"[dim]{msg}[/dim]"))

    model.save(MODEL_PATH)
    console.print(f"\n[bold green]✓ Model kaydedildi: {MODEL_PATH}[/bold green]")
    console.print("[green]Artık 'query-db' komutunda AI tahminleri kullanılacak![/green]\n")


def main():
    print_header()
    agent = HermesAgent()
    
    console.print("[bold blue]Booting core logic...[/bold blue]")
    try:
        agent.initialize_sequence()
    except Exception as e:
        console.print(f"[bold red]Initialization failed. Error: {e}[/bold red]")
        sys.exit(1)

    # AI modeli durumunu kontrol et
    from hermes_db.trajectory_ai import MODEL_PATH
    import os
    if os.path.exists(MODEL_PATH):
        console.print("[green]✓ Eğitilmiş AI modeli bulundu. query-db AI tahminleri kullanacak.[/green]")
    else:
        console.print("[yellow]⚠ AI modeli eğitilmemiş. 'train' komutu ile eğitebilirsiniz. (Şimdilik fizik motoru kullanılacak)[/yellow]")
        
    console.print("\n[bold green]System Ready. Waiting for input...[/bold green]")
    console.print("Commands: [bold]train[/bold] (AI eğit), [bold]query-db[/bold] (enkaz tahmini), [bold]sim[/bold] (fırlatma sim), [bold]ledger[/bold] (kayıtlar), [bold]quit[/bold]\n")
    
    while True:
        try:
            cmd = input("HERMES> ").strip().lower()
            if cmd in ["quit", "q", "exit"]:
                console.print("[yellow]Shutting down HERMES engine...[/yellow]")
                break
            elif cmd == "sim":
                simulate_mission(agent)
            elif cmd == "ledger":
                fetch_ledger()
            elif cmd == "query-db":
                query_hermes_db()
            elif cmd == "train":
                train_ai()
            elif cmd == "":
                continue
            else:
                console.print("[red]Bilinmeyen komut. Komutlar: train, query-db, sim, ledger, quit[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down HERMES engine...[/yellow]")
            break

if __name__ == "__main__":
    main()
