## Apple HIG Look Rules

Source: Jesse Rurka's Apple design reel (https://www.instagram.com/reel/DeW9hxyAMHi/), the allexp1 `apple-hig` skill (skills.sh summary page only; its body was not fully readable), and Apple's Human Interface Guidelines. Web rules only; UB rules and `ui-behaviour.md` win on any clash.

- **Hierarchy:** one primary action per screen, drawn as the most prominent control; every other action is visibly quieter.
- **Clarity:** content is the star; chrome (borders, shadows, fills) never competes with it, so drop any decoration that carries no meaning.
- **Deference:** controls and bars sit behind the content in weight and colour, never louder than the data they frame.
- **Type scale:** use a small fixed set of sizes (title, headline, body, caption) and tell levels apart by weight and size, never by many colours.
- **Hero planes:** a hero is built in three planes: huge type at the back, the subject in the middle, the buttons on top.
- **One size contrast:** on a hero, one thing is huge and the rest stay at body or caption size, with no middle sizes; the fixed type scale above still holds.
- **Body text:** body copy is at least 16 px (also stops iOS input zoom), with line height about 1.4 to 1.5 times the size.
- **Spacing grid:** all gaps and padding come from one 4 px or 8 px step scale (Tailwind's spacing steps); never an odd one-off value.
- **Grouping:** related items sit closer to each other than to unrelated ones, so spacing, not boxes or rules, shows the groups.
- **Alignment:** items that relate share one edge; a screen has few alignment lines, kept consistent.
- **Stacked text:** a stack of hero text is left aligned, never centred, and grouped by closeness: the heading sits with its image, then the price and the button sit together.
- **Where these apply:** hero planes, one size contrast and stacked text cover hero and marketing layouts only; on dashboards, tables and forms the dashboard, table and form rules win.
- **Margins:** keep the same page margin on both sides, and keep text off the screen edge (UB-4 and the mobile edge rules still apply).
- **Colour meaning:** one accent colour marks what is tappable; colour is never the only signal of state (pair it with text or an icon).
- **Destructive styling:** a destructive action uses the shared danger style and is never the default or primary button.
- **Contrast:** secondary text still meets 4.5:1; never fade text with opacity to make it secondary, pick a lower-emphasis theme colour instead.
- **Concentric corners:** a rounded element inside a rounded container uses the container radius minus the padding between them.
- **Depth:** layers (a sheet over a page, a menu over a row) get a soft shadow or a dimmed backdrop so the order of layers is clear.
- **Plain labels:** a button names its result in a verb ("Save changes"); no jargon, no all caps.
