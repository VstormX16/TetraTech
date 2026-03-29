"""
HERMES Physics Engine - Roket Yörünge ve Balistik Düşüş Simülatörü
Çok aşamalı roketlerin yükseliş yörüngesini simüle eder ve
ayrılan parçaların düşüş noktalarını fizik hesaplamasıyla belirler.
"""
import numpy as np

# ══════════════════════════════════════════════════════════════
# SABİTLER
# ══════════════════════════════════════════════════════════════
G0 = 9.80665        # Standart yerçekimi (m/s²)
R_EARTH = 6.371e6   # Dünya yarıçapı (m)
RHO0 = 1.225        # Deniz seviyesi hava yoğunluğu (kg/m³)
H_SCALE = 8500.0    # Atmosfer ölçek yüksekliği (m)


def atm_density(alt_m, humidity=0.0):
    """Üstel atmosfer modeli, neme bağlı ufak yoğunluk değişimi."""
    if alt_m > 200000:
        return 0.0
    # Nem artarsa hava yoğunluğu bir miktar azalır (su buharı havadan hafiftir)
    mod_rho0 = RHO0 * (1.0 - (humidity / 100.0) * 0.02)
    return mod_rho0 * np.exp(-alt_m / H_SCALE)


def gravity(alt_m):
    """Yüksekliğe bağlı yerçekimi."""
    return G0 * (R_EARTH / (R_EARTH + alt_m)) ** 2


class RocketPhysicsEngine:
    """
    Çok aşamalı roket yükseliş ve balistik düşüş simülatörü.
    """

    def simulate_ascent(self, stages, wind_speed=0.0, humidity=50.0, launch_alt=0.0, dt=1.0):
        """
        Çok aşamalı roket yükselişini simüle eder.
        Çevresel faktörleri (rüzgar, nem, rakım) hesaba katar.
        """
        alt = launch_alt
        vel = 0.1
        gamma = np.radians(88.0)   # Dikey'e yakın başlangıç
        downrange = 0.0

        results = []

        for si, stage in enumerate(stages):
            thrust = stage['thrust_kn'] * 1000.0
            m_prop = stage['propellant_mass_kg']
            m_empty = stage['empty_mass_kg']
            burn_t = stage['burn_time_s']
            diam = stage.get('diameter_m', 3.0)
            area = np.pi * (diam / 2.0) ** 2
            cd = 0.30

            upper_mass = sum(
                s['propellant_mass_kg'] + s['empty_mass_kg']
                for s in stages[si + 1:]
            )

            mass = m_prop + m_empty + upper_mass
            fuel_rate = m_prop / burn_t if burn_t > 0 else 0.0

            t = 0.0
            while t < burn_t:
                rho = atm_density(alt, humidity)
                g = gravity(alt)

                # Rüzgar etkisini sürüklenmeye (drag) yansıt
                effective_vel = vel + wind_speed * np.cos(gamma)
                drag = 0.5 * rho * effective_vel ** 2 * cd * area
                
                a_thrust = thrust / mass if mass > 0 else 0
                a_drag = drag / mass if mass > 0 else 0
                a_tan = a_thrust - a_drag - g * np.sin(gamma)

                if vel > 10 and alt > 300:
                    dg = -(g / vel - vel / (R_EARTH + alt)) * np.cos(gamma) * dt
                else:
                    dg = 0.0

                vel += a_tan * dt
                vel = max(vel, 0.01)
                gamma += dg
                gamma = np.clip(gamma, -np.pi / 2, np.pi / 2)

                alt += vel * np.sin(gamma) * dt
                
                # Rüzgarın yanal sürüklemesini ekle
                wind_drift = wind_speed * dt * 0.1
                downrange += (vel * np.cos(gamma) * dt) + wind_drift

                mass -= fuel_rate * dt
                if mass < m_empty + upper_mass:
                    mass = m_empty + upper_mass

                t += dt
                if alt < -500:
                    break

            results.append({
                'stage_num': si + 1,
                'name': stage.get('name', f'Stage {si+1}'),
                'sep_alt_m': max(alt, 0),
                'sep_vel_ms': vel,
                'sep_angle_rad': gamma,
                'sep_downrange_m': downrange * 0.2, # Kullanıcı isteği: Mesafeleri %20'ye düşür
                'empty_mass_kg': m_empty,
                'diameter_m': diam,
            })

        return results

    def simulate_ballistic_fall(self, sep_alt, sep_vel, sep_angle,
                                 mass, diameter, wind_speed=0.0, humidity=50.0, dt=1.0):
        """
        Ayrılan bir kademenin motorsuzu balistik düşüşünü simüle eder.
        Dönüş: ayrılma noktasından itibaren ek menzil (km).
        """
        area = np.pi * (diameter / 2.0) ** 2
        cd = 0.50
        alt = sep_alt
        vel = sep_vel
        gamma = sep_angle
        extra_dr = 0.0
        i = 0

        while alt > 0 and i < 300000:
            rho = atm_density(alt, humidity)
            g = gravity(alt)
            
            effective_vel = vel + wind_speed * np.cos(gamma)
            drag = 0.5 * rho * effective_vel ** 2 * cd * area if vel > 0 else 0

            a_drag = drag / mass if mass > 0 else 0
            a_tan = -a_drag - g * np.sin(gamma)

            if vel > 1:
                dg = -(g / vel - vel / (R_EARTH + alt)) * np.cos(gamma) * dt
            else:
                dg = 0.0

            vel += a_tan * dt
            if vel < 0:
                vel = 0.01

            gamma += dg
            alt += vel * np.sin(gamma) * dt
            
            wind_drift = wind_speed * dt * 0.1
            extra_dr += (vel * np.cos(gamma) * dt) + wind_drift
            i += 1

        return (extra_dr / 1000.0) * 0.2 # Kullanıcı isteği: Mesafeleri %20'ye düşür

    def compute_stage_impacts(self, stages, wind_speed=0.0, humidity=50.0, launch_alt=0.0):
        """
        Her aşamanın fırlatma noktasından toplam düşüş mesafesini hesaplar.
        """
        seps = self.simulate_ascent(stages, wind_speed, humidity, launch_alt)
        impacts = []
        for sc in seps:
            fall_km = self.simulate_ballistic_fall(
                sc['sep_alt_m'], sc['sep_vel_ms'], sc['sep_angle_rad'],
                sc['empty_mass_kg'], sc['diameter_m'], wind_speed, humidity
            )
            total_km = sc['sep_downrange_m'] / 1000.0 + fall_km
            impacts.append({
                'stage_num': sc['stage_num'],
                'name': sc['name'],
                'sep_alt_km': sc['sep_alt_m'] / 1000.0,
                'sep_vel_ms': sc['sep_vel_ms'],
                'total_downrange_km': max(total_km, 0),
            })
        return impacts


def generate_training_data(num_samples=3000, verbose=True):
    """
    Rastgele roket konfigürasyonları oluşturup fizik motoruyla simüle eder.
    Sinir ağı eğitimi için (X, y) çiftleri üretir.
    X: [thrust_kn, prop_mass, empty_mass, burn_time, diameter, upper_mass, stage_num, wind_speed, humidity, launch_alt]
    y: [total_downrange_km]
    """
    engine = RocketPhysicsEngine()
    X_list, y_list = [], []
    success = 0

    for i in range(num_samples):
        wind = np.random.uniform(-30, 30) # m/s
        humid = np.random.uniform(10, 100) # %
        l_alt = np.random.uniform(0, 3000) # m
        
        n_stages = np.random.choice([1, 2, 3], p=[0.15, 0.40, 0.45])
        stages = []

        for s in range(n_stages):
            if s == 0:
                thrust = np.random.uniform(3000, 45000)
                prop_m = np.random.uniform(80000, 2500000)
                empty_m = np.random.uniform(8000, 180000)
                burn_t = np.random.uniform(90, 200)
                diam = np.random.uniform(2.5, 11.0)
            elif s == 1:
                thrust = np.random.uniform(600, 8000)
                prop_m = np.random.uniform(25000, 500000)
                empty_m = np.random.uniform(2500, 50000)
                burn_t = np.random.uniform(150, 500)
                diam = np.random.uniform(2.0, 10.0)
            else:
                thrust = np.random.uniform(200, 2500)
                prop_m = np.random.uniform(8000, 150000)
                empty_m = np.random.uniform(1000, 25000)
                burn_t = np.random.uniform(100, 500)
                diam = np.random.uniform(1.5, 8.0)

            # TWR kontrolü (>1.1 olmalı)
            total_above = sum(st['propellant_mass_kg'] + st['empty_mass_kg'] for st in stages)
            total = prop_m + empty_m + total_above
            twr = (thrust * 1000) / (total * G0)
            if s == 0 and twr < 1.15:
                thrust = 1.2 * total * G0 / 1000

            stages.append({
                'name': f'S{s+1}',
                'thrust_kn': thrust,
                'propellant_mass_kg': prop_m,
                'empty_mass_kg': empty_m,
                'burn_time_s': burn_t,
                'diameter_m': diam,
            })

        try:
            impacts = engine.compute_stage_impacts(stages, wind_speed=wind, humidity=humid, launch_alt=l_alt)
            for imp in impacts:
                si = imp['stage_num'] - 1
                s = stages[si]
                upper_m = sum(
                    st['propellant_mass_kg'] + st['empty_mass_kg']
                    for st in stages[si + 1:]
                )
                features = [
                    s['thrust_kn'],
                    s['propellant_mass_kg'],
                    s['empty_mass_kg'],
                    s['burn_time_s'],
                    s['diameter_m'],
                    upper_m,
                    float(imp['stage_num']),
                    wind,
                    humid,
                    l_alt
                ]
                dr = imp['total_downrange_km']
                if dr > 0:
                    X_list.append(features)
                    y_list.append(dr)
                    success += 1
        except Exception:
            continue

        if verbose and (i + 1) % 500 == 0:
            print(f"  [PhysicsEngine] Simulated {i+1}/{num_samples} rockets, {success} valid samples")

    return np.array(X_list), np.array(y_list)
