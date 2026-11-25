/**
 * DAKSHU AI - Interactive 3D Companion Orb & Particle Visualization
 * Powered by Three.js
 */

class DakshuOrbVisualizer {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.isMini = options.isMini || false;
    this.state = 'idle'; // 'idle', 'listening', 'thinking', 'responding'
    this.targetState = 'idle';
    this.clock = new THREE.Clock();

    // Mouse interaction tracking
    this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    this.audioLevel = 0.0; // Dynamic mic audio / speech reactivity

    // Color definitions per state
    this.stateColors = {
      idle: {
        core: new THREE.Color(0x7928ca),
        glow: new THREE.Color(0x3b82f6),
        wireframe: new THREE.Color(0x06b6d4),
        particles: new THREE.Color(0xa855f7),
        speed: 1.0,
        distortion: 0.15
      },
      listening: {
        core: new THREE.Color(0x00f2fe),
        glow: new THREE.Color(0x06b6d4),
        wireframe: new THREE.Color(0x38bdf8),
        particles: new THREE.Color(0x00f2fe),
        speed: 2.2,
        distortion: 0.35
      },
      thinking: {
        core: new THREE.Color(0xa855f7),
        glow: new THREE.Color(0xec4899),
        wireframe: new THREE.Color(0xf59e0b),
        particles: new THREE.Color(0xf43f5e),
        speed: 3.5,
        distortion: 0.45
      },
      responding: {
        core: new THREE.Color(0x06b6d4),
        glow: new THREE.Color(0x10b981),
        wireframe: new THREE.Color(0x00f2fe),
        particles: new THREE.Color(0x34d399),
        speed: 2.0,
        distortion: 0.28
      }
    };

    this.currentColor = {
      core: this.stateColors.idle.core.clone(),
      glow: this.stateColors.idle.glow.clone(),
      wireframe: this.stateColors.idle.wireframe.clone(),
      particles: this.stateColors.idle.particles.clone(),
      speed: 1.0,
      distortion: 0.15
    };

    this.init();
  }

  init() {
    const width = this.container.clientWidth || 300;
    const height = this.container.clientHeight || 300;

    // 1. Scene
    this.scene = new THREE.Scene();

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    this.camera.position.z = this.isMini ? 3.8 : 4.6;

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.container.appendChild(this.renderer.domElement);

    // 4. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    this.scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0xa855f7, 2, 50);
    pointLight1.position.set(5, 5, 5);
    this.scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x00f2fe, 2, 50);
    pointLight2.position.set(-5, -5, 5);
    this.scene.add(pointLight2);

    this.lights = { p1: pointLight1, p2: pointLight2 };

    // 5. Geometry & Meshes
    this.createOrb();
    this.createWireframeCage();
    if (!this.isMini) {
      this.createParticles();
    }

    // 6. Event Listeners
    window.addEventListener('resize', () => this.onWindowResize());
    if (!this.isMini) {
      window.addEventListener('mousemove', (e) => this.onMouseMove(e));
    }

    // 7. Start Animation Loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  createOrb() {
    // Detailed subdivided sphere for wave vertex displacement
    const detail = this.isMini ? 32 : 64;
    this.orbGeometry = new THREE.SphereGeometry(1.2, detail, detail);

    // Save base vertex positions for wave calculations
    this.basePositions = this.orbGeometry.attributes.position.clone();

    this.orbMaterial = new THREE.MeshStandardMaterial({
      color: this.currentColor.core,
      roughness: 0.15,
      metalness: 0.85,
      emissive: this.currentColor.glow,
      emissiveIntensity: 0.45,
      transparent: true,
      opacity: 0.92
    });

    this.orbMesh = new THREE.Mesh(this.orbGeometry, this.orbMaterial);
    this.scene.add(this.orbMesh);
  }

  createWireframeCage() {
    const cageGeo = new THREE.IcosahedronGeometry(1.4, this.isMini ? 1 : 2);
    this.cageMaterial = new THREE.MeshBasicMaterial({
      color: this.currentColor.wireframe,
      wireframe: true,
      transparent: true,
      opacity: 0.25
    });

    this.cageMesh = new THREE.Mesh(cageGeo, this.cageMaterial);
    this.scene.add(this.cageMesh);
  }

  createParticles() {
    const particleCount = 450;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const scales = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      const radius = 2.0 + Math.random() * 2.8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      scales[i] = Math.random() * 0.05 + 0.02;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    this.particleMaterial = new THREE.PointsMaterial({
      color: this.currentColor.particles,
      size: 0.04,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending
    });

    this.particleSystem = new THREE.Points(geometry, this.particleMaterial);
    this.scene.add(this.particleSystem);
  }

  onMouseMove(e) {
    this.mouse.targetX = (e.clientX / window.innerWidth) * 2 - 1;
    this.mouse.targetY = -(e.clientY / window.innerHeight) * 2 + 1;
  }

  onWindowResize() {
    if (!this.container) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  setState(newState) {
    if (this.stateColors[newState]) {
      this.state = newState;
    }
  }

  setAudioLevel(level) {
    this.audioLevel = THREE.MathUtils.clamp(level, 0, 1);
  }

  updateDisplacements(time) {
    const positions = this.orbGeometry.attributes.position;
    const base = this.basePositions;
    const speed = this.currentColor.speed;
    const distortion = this.currentColor.distortion + (this.audioLevel * 0.4);

    for (let i = 0; i < positions.count; i++) {
      const u = base.getX(i);
      const v = base.getY(i);
      const w = base.getZ(i);

      // Spherical harmonic waves
      const wave1 = Math.sin(u * 2.5 + time * speed * 2.0) * Math.cos(v * 2.5 + time * speed * 1.5);
      const wave2 = Math.cos(w * 3.0 + time * speed * 1.8) * 0.5;
      const totalDisplacement = 1.0 + (wave1 + wave2) * distortion * 0.25;

      positions.setXYZ(i, u * totalDisplacement, v * totalDisplacement, w * totalDisplacement);
    }

    positions.needsUpdate = true;
    this.orbGeometry.computeVertexNormals();
  }

  animate() {
    requestAnimationFrame(this.animate);

    const delta = this.clock.getDelta();
    const elapsedTime = this.clock.getElapsedTime();

    // Smooth state transitions via LERP
    const target = this.stateColors[this.state];
    const lerpFactor = 0.05;

    this.currentColor.core.lerp(target.core, lerpFactor);
    this.currentColor.glow.lerp(target.glow, lerpFactor);
    this.currentColor.wireframe.lerp(target.wireframe, lerpFactor);
    this.currentColor.particles.lerp(target.particles, lerpFactor);
    this.currentColor.speed = THREE.MathUtils.lerp(this.currentColor.speed, target.speed, lerpFactor);
    this.currentColor.distortion = THREE.MathUtils.lerp(this.currentColor.distortion, target.distortion, lerpFactor);

    // Apply colors to materials
    this.orbMaterial.color.copy(this.currentColor.core);
    this.orbMaterial.emissive.copy(this.currentColor.glow);
    this.cageMaterial.color.copy(this.currentColor.wireframe);
    if (this.particleMaterial) {
      this.particleMaterial.color.copy(this.currentColor.particles);
    }

    // Vertex wave pulse
    this.updateDisplacements(elapsedTime);

    // Smooth mouse tilt tracking
    this.mouse.x = THREE.MathUtils.lerp(this.mouse.x, this.mouse.targetX, 0.05);
    this.mouse.y = THREE.MathUtils.lerp(this.mouse.y, this.mouse.targetY, 0.05);

    // Rotate meshes
    this.orbMesh.rotation.y += 0.008 * this.currentColor.speed;
    this.orbMesh.rotation.x = this.mouse.y * 0.35;
    this.orbMesh.rotation.z = -this.mouse.x * 0.35;

    this.cageMesh.rotation.y -= 0.005 * this.currentColor.speed;
    this.cageMesh.rotation.x += 0.003;

    // Breathing pulse scale
    const breath = 1.0 + Math.sin(elapsedTime * 1.8) * 0.04 + (this.audioLevel * 0.18);
    this.orbMesh.scale.set(breath, breath, breath);

    if (this.particleSystem) {
      this.particleSystem.rotation.y += 0.002 * this.currentColor.speed;
      this.particleSystem.rotation.x = this.mouse.y * 0.15;
    }

    this.renderer.render(this.scene, this.camera);
  }
}

// Global initialization helper
window.DakshuOrb = DakshuOrbVisualizer;

