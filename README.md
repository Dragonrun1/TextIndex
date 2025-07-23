# TextIndex

This is [the repository for **TextIndex**](https://github.com/mattgemmell/TextIndex), a simple syntax for creating indexes (in the end-of-a-book sense) in Markdown or other text documents. It was created by [Matt Gemmell](https://mattgemmell.scot), and is made available under the [GPL-3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

Feature requests, bug reports, and general discussion are welcomed; you can [use the issue tracker here](https://github.com/mattgemmell/TextIndex/issues).

## Documentation

Since github doesn't allow the use of custom CSS in hosted README files like this one, please **[read the TextIndex documentation here](https://mattgemmell.scot/textindex)** for illustrated examples, syntax, etc.


## Purpose

While working on my [pandoc-based Markdown publishing system](https://github.com/mattgemmell/pandoc-publish), I became aware that the creation of indexes (in the end-of-a-book sense) from plain text documents such as Markdown files was a convoluted process, often involving intermediate markup formats or external files.

My aim was to provide a documented-integrated 80% solution, allowing the annotation of terms for inclusion in a generated index, including many of the subtleties and formatting conventions of professionally-produced manual indexes. The result is TextIndex.

Its formatting is primarily of the flush-and-hang (indented) style, and tries to follow many of the principles described in [the indexing guide of the Chicago Manual of Style](https://www.chicagomanualofstyle.org/book/ed18/part3/ch15/toc.html), within the constraints of simplicity.

Note that TextIndex can generate hyperlinked reference-ID-based indexes for non-paginated formats such as HTML or ePub ebooks, and also true page-number-based indexes for paginated formats such as print and PDF, making it useful in online and digital contexts too (even though indexes are less commonly found outside the printed or printable realm).

See [the documentation](https://mattgemmell.scot/textindex) for more.
