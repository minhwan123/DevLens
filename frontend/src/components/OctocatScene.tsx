import { useMemo, useRef, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Line, Sparkles, Text } from '@react-three/drei'
import * as THREE from 'three'

const DARK = '#14171f'
const DARKER = '#0e1116'
const SKIN = '#dba97c'

// A seamless "infinity cove" (photo-studio cyclorama): a flat floor that curves
// smoothly into a flat back wall via a quarter-circle bend, extruded across width.
// Built once as plain profile math rather than a shader so it costs nothing extra
// to light/shadow — it's just a normal mesh.
function useInfinityCoveGeometry({
  width = 16,
  floorY = -1.5,
  floorDepth = 6,
  bendRadius = 2.5,
  wallTop = 6,
}: {
  width?: number
  floorY?: number
  floorDepth?: number
  bendRadius?: number
  wallTop?: number
} = {}) {
  return useMemo(() => {
    const arcSamples = 20
    const profile: [number, number][] = []

    // flat floor: from just under the camera out to where the bend starts
    profile.push([floorY, -2])
    profile.push([floorY, floorDepth - bendRadius])

    // quarter-circle bend: floor (horizontal tangent) -> wall (vertical tangent)
    const yc = floorY + bendRadius
    const zc = floorDepth - bendRadius
    for (let i = 1; i <= arcSamples; i++) {
      const theta = (Math.PI / 2) * (i / arcSamples)
      profile.push([yc - bendRadius * Math.cos(theta), zc + bendRadius * Math.sin(theta)])
    }

    // flat back wall: straight up from where the bend ends
    profile.push([wallTop, floorDepth])

    const positions: number[] = []
    const indices: number[] = []
    const halfW = width / 2
    for (const [y, z] of profile) {
      positions.push(-halfW, y, -z, halfW, y, -z)
    }
    for (let row = 0; row < profile.length - 1; row++) {
      const a = row * 2
      const b = row * 2 + 1
      const c = (row + 1) * 2
      const d = (row + 1) * 2 + 1
      indices.push(a, c, b, b, c, d)
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
    geometry.setIndex(indices)
    geometry.computeVertexNormals()
    return geometry
  }, [width, floorY, floorDepth, bendRadius, wallTop])
}

function Ear({ side }: { side: 1 | -1 }) {
  return (
    <group position={[side * 0.55, 0.95, -0.05]} rotation={[0, 0, side * -0.3]}>
      <mesh castShadow scale={[1, 1.15, 0.8]}>
        <sphereGeometry args={[0.34, 20, 20, 0, Math.PI * 2, 0, Math.PI * 0.65]} />
        <meshStandardMaterial color={DARK} roughness={0.7} />
      </mesh>
    </group>
  )
}

function Eye({ x }: { x: number }) {
  return (
    <group position={[x, 0.42, 1.14]}>
      <mesh scale={[1, 1.15, 0.35]}>
        <sphereGeometry args={[0.13, 20, 20]} />
        <meshStandardMaterial color="#f5f2ea" roughness={0.4} />
      </mesh>
      <mesh position={[0, 0, 0.06]} scale={[1, 1, 0.45]}>
        <sphereGeometry args={[0.075, 16, 16]} />
        <meshStandardMaterial color="#6b3a2a" roughness={0.35} />
      </mesh>
      <mesh position={[0.025, 0.03, 0.1]}>
        <sphereGeometry args={[0.018, 8, 8]} />
        <meshStandardMaterial color="#ffffff" />
      </mesh>
    </group>
  )
}

function Whiskers({ side }: { side: 1 | -1 }) {
  const rows = [
    [
      [side * 0.35, 0.44, 1.05],
      [side * 0.95, 0.5, 0.88],
    ],
    [
      [side * 0.35, 0.4, 1.06],
      [side * 0.97, 0.4, 0.8],
    ],
    [
      [side * 0.35, 0.36, 1.05],
      [side * 0.93, 0.3, 0.74],
    ],
  ] as const

  return (
    <>
      {rows.map((points, i) => (
        <Line key={i} points={points} color="#9aa4b2" lineWidth={1} transparent opacity={0.55} />
      ))}
    </>
  )
}

function Tail() {
  const group = useRef<THREE.Group>(null)

  const curve = useMemo(
    () =>
      new THREE.CatmullRomCurve3([
        new THREE.Vector3(-0.5, -0.5, -0.6),
        new THREE.Vector3(-0.95, -0.25, -0.9),
        new THREE.Vector3(-1.28, 0.15, -0.65),
        new THREE.Vector3(-1.15, 0.5, -0.25),
        new THREE.Vector3(-0.8, 0.62, 0.05),
      ]),
    [],
  )

  const cupPositions = useMemo(() => {
    const points: THREE.Vector3[] = []
    for (let t = 0.15; t <= 0.95; t += 0.16) {
      points.push(curve.getPointAt(t))
    }
    return points
  }, [curve])

  useFrame(({ clock }) => {
    if (!group.current) return
    const t = clock.getElapsedTime()
    group.current.rotation.y = Math.sin(t * 0.9) * 0.08
    group.current.rotation.z = Math.cos(t * 0.7) * 0.04
  })

  return (
    <group ref={group}>
      <mesh castShadow>
        <tubeGeometry args={[curve, 32, 0.13, 8, false]} />
        <meshStandardMaterial color={DARK} roughness={0.6} />
      </mesh>
      {cupPositions.map((p, i) => (
        <mesh key={i} position={p} castShadow>
          <sphereGeometry args={[0.055, 8, 8]} />
          <meshStandardMaterial color="#a9d8e6" roughness={0.4} emissive="#3fa0c0" emissiveIntensity={0.15} />
        </mesh>
      ))}
    </group>
  )
}

function Arm({ side }: { side: 1 | -1 }) {
  return (
    <group position={[side * 0.85, -0.15, 0.75]} rotation={[0.9, 0, side * -0.15]}>
      <mesh castShadow>
        <capsuleGeometry args={[0.14, 0.5, 4, 8]} />
        <meshStandardMaterial color={DARK} roughness={0.65} />
      </mesh>
    </group>
  )
}

function Laptop({
  onEnter,
  hovered,
  setHovered,
}: {
  onEnter: () => void
  hovered: boolean
  setHovered: (v: boolean) => void
}) {
  return (
    <group position={[0, -0.25, 1.35]}>
      <mesh position={[0, -0.42, 0.32]} rotation={[-1.35, 0, 0]} castShadow>
        <boxGeometry args={[1.5, 0.9, 0.05]} />
        <meshStandardMaterial color="#3a3f4a" metalness={0.5} roughness={0.35} />
      </mesh>

      <mesh
        position={[0, 0.05, 0]}
        onClick={(e) => {
          e.stopPropagation()
          onEnter()
        }}
        onPointerOver={(e) => {
          e.stopPropagation()
          setHovered(true)
          document.body.style.cursor = 'pointer'
        }}
        onPointerOut={() => {
          setHovered(false)
          document.body.style.cursor = 'auto'
        }}
      >
        <boxGeometry args={[1.5, 1.0, 0.06]} />
        <meshStandardMaterial color="#2a2f3a" roughness={0.4} />
      </mesh>
      <mesh position={[0, 0.05, 0.034]}>
        <planeGeometry args={[1.34, 0.86]} />
        <meshStandardMaterial
          color={DARKER}
          emissive="#3fb950"
          emissiveIntensity={hovered ? 0.35 : 0.16}
        />
      </mesh>
      <Text position={[0, 0.18, 0.05]} fontSize={0.13} color="#3fb950" anchorX="center" anchorY="middle">
        {'<DevLens>'}
      </Text>
      <Text
        position={[0, -0.08, 0.05]}
        fontSize={0.052}
        color="#9aa4b2"
        anchorX="center"
        anchorY="middle"
        lineHeight={1.6}
        textAlign="center"
      >
        {'Analyze Your GitHub.\nShape Your Career.'}
      </Text>
    </group>
  )
}

function Character({ onEnter }: { onEnter: () => void }) {
  const group = useRef<THREE.Group>(null)
  const [hovered, setHovered] = useState(false)

  useFrame(({ clock, pointer }) => {
    if (!group.current) return
    const t = clock.getElapsedTime()
    group.current.position.y = Math.sin(t * 1.1) * 0.06
    group.current.rotation.y += (pointer.x * 0.25 - group.current.rotation.y) * 0.04
    group.current.rotation.x += (-pointer.y * 0.1 - group.current.rotation.x) * 0.04
  })

  return (
    <group ref={group}>
      {/* body */}
      <mesh position={[0, 0, 0]} scale={[1, 1, 0.9]} castShadow>
        <sphereGeometry args={[1.0, 32, 32]} />
        <meshStandardMaterial color={DARK} roughness={0.7} />
      </mesh>

      <Ear side={-1} />
      <Ear side={1} />

      {/* face */}
      <mesh position={[0, 0.35, 0.82]} scale={[1, 0.85, 0.4]} castShadow>
        <sphereGeometry args={[0.55, 32, 32]} />
        <meshStandardMaterial color={SKIN} roughness={0.8} />
      </mesh>

      <Eye x={-0.2} />
      <Eye x={0.2} />

      {/* nose */}
      <mesh position={[0, 0.28, 1.18]}>
        <sphereGeometry args={[0.035, 8, 8]} />
        <meshStandardMaterial color="#3a2a20" roughness={0.5} />
      </mesh>

      {/* smile */}
      <mesh position={[0, 0.17, 1.2]} rotation={[Math.PI / 2, 0, Math.PI]}>
        <torusGeometry args={[0.14, 0.02, 8, 16, Math.PI]} />
        <meshStandardMaterial color="#3a2a20" roughness={0.6} />
      </mesh>

      <Whiskers side={-1} />
      <Whiskers side={1} />

      <Arm side={-1} />
      <Arm side={1} />

      <Tail />

      <Laptop onEnter={onEnter} hovered={hovered} setHovered={setHovered} />
    </group>
  )
}

function ZoomRig({
  zooming,
  overlayRef,
  onDone,
}: {
  zooming: boolean
  overlayRef: React.RefObject<HTMLDivElement | null>
  onDone: () => void
}) {
  const { camera } = useThree()
  const progress = useRef(0)
  const done = useRef(false)

  useFrame((_, delta) => {
    if (!zooming || done.current) return
    progress.current = Math.min(1, progress.current + delta / 0.6)
    const eased = 1 - Math.pow(1 - progress.current, 3)
    camera.position.z = THREE.MathUtils.lerp(6.5, 2.0, eased)
    camera.position.y = THREE.MathUtils.lerp(0.25, -0.2, eased)
    camera.lookAt(0, -0.15, 1.35)
    if (overlayRef.current) {
      overlayRef.current.style.opacity = String((Math.max(0, eased - 0.75) / 0.25) * 0.7)
    }
    if (progress.current >= 1 && !done.current) {
      done.current = true
      onDone()
    }
  })

  return null
}

export function OctocatScene({ onEnter }: { onEnter: () => void }) {
  const [zooming, setZooming] = useState(false)
  const overlayRef = useRef<HTMLDivElement>(null)
  const coveGeometry = useInfinityCoveGeometry()

  const handleEnter = () => {
    if (zooming) return
    setZooming(true)
  }

  return (
    <div className="octocat-scene">
      <Canvas
        shadows
        camera={{ position: [0, 0.25, 6.5], fov: 34 }}
        onCreated={({ gl }) => gl.setClearColor('#0a0e14')}
      >
        <ambientLight intensity={1.2} />
        <directionalLight position={[3, 5, 4]} intensity={1.0} castShadow />
        <pointLight position={[-3, 1, 2]} intensity={0.35} color="#3fb950" />
        <spotLight
          position={[0, 5, 1]}
          angle={0.75}
          penumbra={0.9}
          intensity={1.6}
          castShadow
          color="#e8ecf1"
        />
        {/* fill light aimed at the backdrop itself so the cove reads as a lit surface, not a void */}
        <pointLight position={[0, 2, -4]} intensity={1.4} color="#3a4656" distance={10} decay={1.2} />
        {/* rim lights: trace the character's silhouette from behind, left/right */}
        <pointLight position={[-1.6, 0.7, -0.6]} intensity={2.2} color="#8fd6ff" distance={5} />
        <pointLight position={[1.6, 0.7, -0.6]} intensity={2.2} color="#3fb950" distance={5} />
        <fog attach="fog" args={['#0a0e14', 9, 22]} />

        <Sparkles count={35} scale={[8, 5, 4]} size={1.6} speed={0.2} color="#3fb950" opacity={0.3} />

        <Character onEnter={handleEnter} />
        <ZoomRig zooming={zooming} overlayRef={overlayRef} onDone={onEnter} />

        <mesh geometry={coveGeometry} receiveShadow>
          <meshStandardMaterial color="#242b38" roughness={0.75} metalness={0.1} side={THREE.DoubleSide} />
        </mesh>
      </Canvas>
      <div ref={overlayRef} className="scene-zoom-overlay" />
    </div>
  )
}
