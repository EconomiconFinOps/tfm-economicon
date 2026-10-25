// Componente canario del arnés de pruebas (JUP-095, tarea 2.3).
//
// No es una pantalla de producto: su único cometido es dar al test
// `HarnessSmoke.test.tsx` un elemento accesible que confirme que el
// arnés (Vitest + Testing Library + jsdom) resuelve JSX/TSX y renderiza
// correctamente. Por eso se mantiene minimal: sin props, sin estado,
// sin estilos (el sistema de diseño se cablea en la tarea 3 de esta
// misma tarjeta).
//
// `role="status"` (en vez de, por ejemplo, un `<div>` sin rol) porque
// el test consulta explícitamente por ese rol ARIA.
//
// El rol `status` define en WAI-ARIA su nombre accesible como
// "nameFrom: author": a diferencia de roles como `button`, el nombre
// NO se calcula a partir del contenido de texto, sino que debe
// declararse explícitamente (aria-label / aria-labelledby). Por eso
// `aria-label` es obligatorio aquí, no un adorno: sin él,
// `getByRole("status", { name: ... })` no encontraría el elemento
// (verificado en fase Green: con solo texto como hijo, el nombre
// accesible calculado es "" y el test falla). El texto visible se
// mantiene además como contenido, duplicando el mensaje, para que el
// canario también sea legible por una persona que inspeccione el DOM.
export function HarnessSmoke(): JSX.Element {
  return (
    <p role="status" aria-label="Entorno de pruebas del frontend operativo">
      Entorno de pruebas del frontend operativo
    </p>
  );
}
