# gobs-learn

L0→L1 coaching on top of **[gobs](https://github.com/wisdom-km/gobs)**.

gobs opens Obsidian and Grok, and saves ordinary notes (explainers, translations).
**gobs-learn** is the separate app for lessons: `/learn` in a session, domain cards,
`gobs-learn start` / `save` / `status`.

Install gobs first (or let pip pull it):

```bash
pip install git+https://github.com/wisdom-km/gobs.git@core
pip install git+https://github.com/wisdom-km/gobs-learn.git
```

```bash
gobs init "/path/to/your/vault"
gobs-learn init "/path/to/your/vault"
gobs-learn start Transformer --no-launch   # create the card only
gobs                                # daily: Obsidian + Grok
# in the session: /learn Transformer
```

```text
gobs-learn init [vault]
gobs-learn start NAME [--no-launch] [--new] [--resume ID]
gobs-learn save --note CARD.md --body-file CARD.md --chat-file LECTURE.md
gobs-learn status
```

Domain cards (`gobs_type: domain`) belong to this app, not to gobs.

## License

MIT. See [LICENSE](LICENSE).
