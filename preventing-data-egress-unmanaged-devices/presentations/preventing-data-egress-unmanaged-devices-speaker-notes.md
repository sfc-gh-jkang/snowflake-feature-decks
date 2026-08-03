# Speaker Notes: Preventing Data Download to Unmanaged Devices

## Presentation Context

Who this is for, what they should be able to do afterwards, and the section map.
Name the audience explicitly (SEs / AEs / customers / architects) because it
changes how much Snowflake-internal shorthand is acceptable.

State GA vs preview vs undocumented here, once, plainly. If any claim in the
deck is field-observed rather than documented, say so in this paragraph — the
person presenting needs to know before a customer asks, not during.

---

## Slide 1: Hero / Overview

**Talking Points:**
- Open with the frame, in the presenter's own words.
- Walk the four stat cards; each should map to a claim the deck later proves.
- Set expectations for the section arc.

**Key Insight:**
The one idea that makes the rest of the deck obvious. If you can't write this in
three sentences, the slide is trying to do too much.

**Common Questions:**
- *Q: Is this GA?*
  A: State it directly. If partly undocumented, say which part and what the
  evidence is.
- *Q: How is this different from <the obvious alternative>?*
  A: Name the alternative and the specific tradeoff.

**References:**
- https://docs.snowflake.com/en/...

---

## Slide N: <Section Name>

**Talking Points:**
- One bullet per point you'd actually say out loud.
- Include the number or the limit — vague guidance doesn't survive contact with
  a customer.

**Key Insight:**
Why this section exists in the arc.

**Common Questions:**
- *Q: ...*
  A: ...

**References:**
- https://docs.snowflake.com/en/...

---

## Notes on writing these

Keep one `## Slide N` block per `<section class="slide">` in the HTML, in the
same order, with the same names. When the two drift, the notes stop being usable
mid-presentation, which is the only moment they matter.

Every factual claim gets a `docs.snowflake.com` link in **References**. A claim
with no link is either wrong or undocumented, and both cases need to be visible
to whoever presents it.
