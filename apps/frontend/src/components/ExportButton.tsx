import { Download, FileText, FileSpreadsheet } from "lucide-react";
import { useState } from "react";

// El origen tipa `data`/`row` como `any` (JUP-095, grupo 5, tarea 5.3). Este
// repo corre con `strict: true` y la tarjeta prohibe introducir `any` nuevo
// (design.md, decision 9), asi que sustituimos por un tipo real: los 5
// dashboards que consumen este boton construyen su `exportData` como un
// array de objetos planos con valores de texto o numero (columnas de
// tabla/KPI), de ahi `Record<string, string | number>` en vez de una
// interfaz mas amplia (p.ej. `unknown`) que obligaria a castear en cada uso.
type ExportRow = Record<string, string | number>;

interface ExportButtonProps {
  data: ExportRow[];
  filename: string;
}

export function ExportButton({ data, filename }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const exportToCSV = () => {
    const headers = Object.keys(data[0] || {});
    const csvContent = [
      headers.join(','),
      ...data.map((row: ExportRow) =>
        headers.map(h => JSON.stringify(row[h] || '')).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}.csv`;
    link.click();
    setIsOpen(false);
  };

  const exportToPDF = () => {
    const content = `
      <html>
        <head>
          <title>${filename}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #1e40af; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #1e40af; color: white; }
          </style>
        </head>
        <body>
          <h1>${filename}</h1>
          <p>Generado: ${new Date().toLocaleString('es-ES')}</p>
          <table>
            <thead>
              <tr>${Object.keys(data[0] || {}).map(h => `<th>${h}</th>`).join('')}</tr>
            </thead>
            <tbody>
              ${data.map((row: ExportRow) =>
                `<tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>`
              ).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `;

    const printWindow = window.open('', '', 'width=800,height=600');
    if (printWindow) {
      printWindow.document.write(content);
      printWindow.document.close();
      printWindow.print();
    }
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#0078d4] to-[#00bcf2] text-white rounded-lg hover:shadow-lg hover:shadow-blue-500/30 transition-all"
      >
        <Download className="w-4 h-4" />
        Exportar Resultados
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-48 bg-[#1a1f2e] rounded-lg shadow-xl border border-[#2d3748] z-20">
            <button
              onClick={exportToCSV}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#232834] transition-colors text-left text-white"
            >
              <FileSpreadsheet className="w-4 h-4 text-green-400" />
              <span>Exportar CSV</span>
            </button>
            <button
              onClick={exportToPDF}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#232834] transition-colors text-left border-t border-[#2d3748] text-white"
            >
              <FileText className="w-4 h-4 text-red-400" />
              <span>Exportar PDF</span>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
