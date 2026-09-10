# Visual system

These are the rules that make the diagrams read as professional rather than dragged-together.
They are topology-agnostic — they hold whether the design has one resource group or five
subscriptions across three tenants.

## Canvas

- **Landscape, sized to its content.** Never force every design onto one sheet size. A reader
  picks *one* design and lives with it, so each page must look right on its own. `Page(w=…)`
  sets the width; `emit()` computes the height from the tallest content plus a margin.
- **Everything on a 10px grid.** `_geo` asserts this. Fractional coordinates are the single
  strongest tell of a hand-dragged diagram.
- **Uniform icon sizes.** 32px for resources in a data band, 26px inside plan boxes, 24px for
  private endpoints and telemetry, 28px for scope corner icons, 18px for a plan's own icon.
  Mixing 31.61 / 38 / 48 in one diagram looks amateur even when nothing else is wrong.

## Scopes

Tenant → subscription → resource group → virtual network → subnet. Nesting must be
**geometrically true**: if a box is drawn inside another it really is contained by it. Keep a
≥20px inset so corner icons have room.

- Each scope carries its icon **straddling its top-left corner**, with the name and a short
  subtitle to the right of the icon, as one label (`scope_corner`).
- Scope labels **always knock out to white**. Without it the container's own top border draws
  straight through the text.
- **Subscription** is the yellow container (`#fff2cc` / `#d6b656`). Tenant is a dashed neutral
  outline. Resource groups are a near-white fill with a light border and a subtle 6px radius.
- **Resource groups are never colour-coded per environment.** The naming convention carries
  that. Colour-coding three identical blocks adds noise and no information.

## Grouping bands

Compute / Networking / Data & secrets / Observability. All four get **identical, quiet**
treatment: a hairline border, no fill, and the label sitting on the top border like a fieldset
legend, knocked out of it. That frees the whole interior for content.

Networking is a band like the others — solid, not dashed — labelled `Networking - <vnet-name>`
without the address space. Subnets inside it are dashed.

## Showing relationships

- **Hosting is containment, never a line.** An app sits inside the plan box that runs it. A
  plan drawn as a caption under an app is not legible; a plan drawn as a container is.
- **A private endpoint sits directly above the resource it fronts**, in the same column,
  joined by a short vertical dotted line. Alignment does most of the explaining. Getting this
  wrong — endpoints in one row, resources in another, lines crossing — is what makes private
  networking unreadable.
- **Many-to-one converges on a shared horizontal** routed through a gap between containers, so
  it crosses no labels (`converge`).
- **Sequences use numbered badges, not edge labels.** Seven labelled arrows will always
  collide; seven badges never do. Put the step text in a separate ordered panel.
- Keep the edge vocabulary small — three styles maximum, and **every style defined in the
  legend must actually be used on a page**. An unused legend entry is a defect.

## Text on the canvas

Labels, resource names and short factual captions belong on the diagram. **Commentary,
trade-offs and risks do not** — they go in a `designs.md` beside the file. A canvas covered in
prose panels reads as generated filler and crowds out the architecture.

## Layers

Four, identically named on every topology page: `Base`, `Networking`, `Observability`,
`Annotations`. All visible by default. This lets a reviewer mute one concern live.

## Pages

A legend page first (icons, line semantics, grouping bands, naming convention, region
placement, how to read it), then one page per design, then any design-independent page such
as an identity/token flow. Number the designs in the kicker: `DESIGN 2 OF 4`.
