export type DestinationNode = {
  id: string;
  label: string;
  /** 선택: 원문 페이지 URL이 확실할 때만 */
  href?: string;
  children?: DestinationNode[];
};

export type DestinationTreeFile = {
  version: number;
  description?: string;
  nodes: DestinationNode[];
};
