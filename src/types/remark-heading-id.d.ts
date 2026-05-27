declare module 'remark-heading-id' {
  import type { Root } from 'mdast';
  import type { Plugin } from 'unified';
  const plugin: Plugin<[], Root>;
  export default plugin;
}
