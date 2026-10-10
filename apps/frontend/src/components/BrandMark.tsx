import primaryMark from "../assets/brand/economicon-primary.png";
import inverseMark from "../assets/brand/economicon-inverse.png";

/** Official dossier artwork, kept intact with its original aspect ratio and clear space. */
export function BrandMark({ inverse = false }: { inverse?: boolean }) {
  return (
    <div className={`brand-mark${inverse ? " brand-mark--inverse" : ""}`}>
      <img src={inverse ? inverseMark : primaryMark} alt="" width={52} height={52} aria-hidden="true" />
      <div>
        <span className="brand-mark__name">Economicon</span>
        <span className="brand-mark__descriptor">FinOps AI Platform</span>
      </div>
    </div>
  );
}
