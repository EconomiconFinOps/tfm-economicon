// Extiende `expect` de Vitest con los matchers de accesibilidad/DOM de
// jest-dom (toBeInTheDocument, toHaveTextContent...). Se carga una vez por
// proceso de test vía `test.setupFiles` en vite.config.ts (JUP-095, grupo 2).
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Testing Library registra su limpieza automática (desmontar cada árbol
// renderizado tras cada test) enganchándose al `afterEach` global si existe.
// Este proyecto usa `globals: false` en vite.config.ts (importa
// describe/it/expect explícitos en cada test, grupo 2): sin un `afterEach`
// global, ese auto-cleanup nunca se registra y el DOM montado por un test
// se filtra al siguiente `it()` del mismo archivo (detectado en el grupo 4:
// dos tests de Separator en el mismo describe se contaminaban entre sí).
// Registrarlo aquí, explícito, es el patrón oficial documentado por
// Testing Library para proyectos sin `globals: true`.
afterEach(cleanup);

// jsdom no implementa ResizeObserver (no hay motor de layout real que
// dispare eventos de redimensionado). `recharts` lo usa dentro de
// `ResponsiveContainer` para medir el contenedor y lo referencia sin
// comprobar si existe: sin este mock, cualquier dashboard con un grafico
// revienta el render con `ResizeObserver is not defined` (verificado en
// JUP-095, grupo 5, antes de portar los dashboards). El mock no necesita
// disparar callbacks: los dashboards no dependen de un tamaño real para
// renderizar su contenido no gráfico (KPIs, tablas), solo de que el
// componente no lance al montarse.
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

// jsdom sombrea `AbortController`/`AbortSignal` con su propia implementación
// (class AbortSignal extends globalObject.EventTarget), pero `Request` se
// queda nativo de Node (undici, jsdom no implementa Fetch). El `Request`
// nativo valida `signal instanceof AbortSignal` contra SU PROPIA clase
// interna, distinta de la de jsdom: cualquier `new Request(url, { signal })`
// construido con un signal de jsdom lanza `TypeError: RequestInit: Expected
// signal ... to be an instance of AbortSignal`. `react-router` 7 construye
// exactamente eso en cada navegación real (`createClientSideRequest`,
// incluso sin loaders), así que sin este parche ninguna prueba que navegue
// de verdad con `createMemoryRouter`/`RouterProvider` puede funcionar
// (verificado en JUP-095, grupo 6, con un repro mínimo sin código de
// producto: un `<Navigate>` desnudo ya revienta).
//
// No hay forma de recuperar el `AbortController` nativo de Node desde aquí
// (ya está sombreado quando arranca el entorno de test, antes de que este
// archivo se ejecute), así que el parche interviene en el otro extremo:
// envuelve `Request` en un `Proxy` que, SOLO si la construcción falla por
// el `signal`, reintenta sin él. No es un polyfill permisivo que ignore
// cualquier error — cualquier otro fallo de `Request` se sigue propagando
// tal cual.
const NativeRequest = globalThis.Request;

globalThis.Request = new Proxy(NativeRequest, {
  construct(target, args) {
    try {
      return Reflect.construct(target, args);
    } catch (error) {
      const [input, init] = args as [unknown, RequestInit | undefined];
      if (init && "signal" in init) {
        const { signal: _signal, ...rest } = init;
        return Reflect.construct(target, [input, rest]);
      }
      throw error;
    }
  }
}) as typeof Request;
