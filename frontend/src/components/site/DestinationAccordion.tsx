import { ChevronRight } from "lucide-react";
import rawTree from "@/data/destination-tree.json";
import type { DestinationNode, DestinationTreeFile } from "@/types/destination";

const data = rawTree as DestinationTreeFile;

function NodeItem({ node }: { node: DestinationNode }) {
  const childList = node.children;
  const hasChildren = Array.isArray(childList) && childList.length > 0;
  const emptyBranch = Array.isArray(childList) && childList.length === 0;

  if (!hasChildren) {
    return (
      <li className="border-b border-[var(--site-border)]/60 py-2.5 text-sm last:border-b-0">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 pl-1">
          {node.href ? (
            <a
              href={node.href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--site-ink)] underline-offset-4 hover:text-[var(--site-accent)] hover:underline"
            >
              {node.label}
            </a>
          ) : (
            <span className="text-[var(--site-ink)]">{node.label}</span>
          )}
          {emptyBranch && (
            <span className="text-xs font-normal text-[var(--site-muted)]">
              (세부 페이지는 기존 Google Sites에서 확인)
            </span>
          )}
        </div>
      </li>
    );
  }

  return (
    <li className="border-b border-[var(--site-border)]/60 last:border-b-0">
      <details className="destination-details group">
        <summary className="flex cursor-pointer list-none items-start gap-2 py-3 pr-1 [&::-webkit-details-marker]:hidden">
          <ChevronRight className="destination-caret mt-0.5 size-4 shrink-0 text-[var(--site-muted)] transition-transform duration-200" />
          <span className="text-sm font-semibold text-[var(--site-ink)]">{node.label}</span>
        </summary>
        <ul className="ml-1 border-l border-[var(--site-border)] pb-2 pl-4">
          {childList!.map((c) => (
            <NodeItem key={c.id} node={c} />
          ))}
        </ul>
      </details>
    </li>
  );
}

export function DestinationAccordion() {
  return (
    <div className="destination-tree rounded-xl border border-[var(--site-border)] bg-white/80 p-2 shadow-sm sm:p-4">
      <p className="mb-3 px-2 text-xs text-[var(--site-muted)] sm:px-3">
        {data.description}
      </p>
      <ul className="divide-y divide-[var(--site-border)]/50">
        {data.nodes.map((n) => (
          <NodeItem key={n.id} node={n} />
        ))}
      </ul>
    </div>
  );
}
