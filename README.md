<!--
Copyright 2020 Pipin Fitriadi <pipinfitriadi@gmail.com>

Licensed under the Microsoft Reference Source License (MS-RSL)

This license governs use of the accompanying software. If you use the
software, you accept this license. If you do not accept the license, do not
use the software.

1. Definitions

The terms "reproduce," "reproduction" and "distribution" have the same
meaning here as under U.S. copyright law.

"You" means the licensee of the software.

"Your company" means the company you worked for when you downloaded the
software.

"Reference use" means use of the software within your company as a reference,
in read only form, for the sole purposes of debugging your products,
maintaining your products, or enhancing the interoperability of your
products with the software, and specifically excludes the right to
distribute the software outside of your company.

"Licensed patents" means any Licensor patent claims which read directly on
the software as distributed by the Licensor under this license.

2. Grant of Rights

(A) Copyright Grant- Subject to the terms of this license, the Licensor
grants you a non-transferable, non-exclusive, worldwide, royalty-free
copyright license to reproduce the software for reference use.

(B) Patent Grant- Subject to the terms of this license, the Licensor grants
you a non-transferable, non-exclusive, worldwide, royalty-free patent
license under licensed patents for reference use.

3. Limitations

(A) No Trademark License- This license does not grant you any rights to use
the Licensor's name, logo, or trademarks.

(B) If you begin patent litigation against the Licensor over patents that
you think may apply to the software (including a cross-claim or counterclaim
in a lawsuit), your license to the software ends automatically.

(C) The software is licensed "as-is." You bear the risk of using it. The
Licensor gives no express warranties, guarantees or conditions. You may have
additional consumer rights under your local laws which this license cannot
change. To the extent permitted under your local laws, the Licensor excludes
the implied warranties of merchantability, fitness for a particular purpose
and non-infringement.
-->

# VOXROWLib

Daftar isi:

<!-- TOC -->

- [VOXROWLib](#voxrowlib)
    - [Source-code](#source-code)
        - [Editor](#editor)
        - [Repositori Git](#repositori-git)
        - [Tata Cara Penulisan Markdown](#tata-cara-penulisan-markdown)
    - [Server](#server)
    - [Lisensi](#lisensi)

<!-- /TOC -->

---

## _Source-code_

### _Editor_

[VSCode](https://code.visualstudio.com/) (Visual Studio Code) dipergunakan untuk
memudahkan dalam penulisan _source-code_.

Beberapa _extension_ VSCode dipasangkan untuk memudahkan penulisan _source-code_,
antara lain:

- [_Auto Markdown TOC_](https://marketplace.visualstudio.com/items?itemName=huntertran.auto-markdown-toc)
- [_Markdownlint_](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)
- [_Python extension for Visual Studio Code_](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

### Repositori Git

[Git](https://git-scm.com/) GUI [Sourcetree](https://www.sourcetreeapp.com/) dapat
dipergunakan untuk memudahkan pengelolaan repositori, pada sistem operasi Windows
atau MacOS.

_Branching model_ [Git-Flow](https://github.com/nvie/gitflow) dari Vincent Driessen
dipergunakan untuk memudahkan pengelolaan _feature_, _release_, dan _hotfix_ di
dalam repositori.

### Tata Cara Penulisan _Markdown_

Beberapa sumber ini dapat dijadikan acuan tata cara penulisan _markdown_:

- [_GitLab: List of supported languages and lexers_](https://github.com/rouge-ruby/rouge/wiki/List-of-supported-languages-and-lexers)
- [_GitLab Markdown_](https://docs.gitlab.com/ee/user/markdown.html)
- [_Wikipedia: Markdown_](https://en.m.wikipedia.org/wiki/Markdown)
- [Berkas readme.md yang dibuat oleh Ben Strahan](https://gist.github.com/benstr/8744304#file-readme-md)

---

## _Server_

Disarankan untuk menggunakan [Ubuntu 18.04 x64](https://ubuntu.com/download/desktop)
(_CPU_ minimal 1 vCore, _RAM_ minimal 512 MB, _Storage_ minimal 10 GB SSD, dan _Bandwidth_
minimal 500 GB), supaya memudahkan pengelolaan _server_ dengan mengunakan _script_
VOXROWLib. Adapun langkah yang harus dipersiapkan adalah sebagai berikut:

1. Pastikan telah ada _source-code_ VOXROWLib di komputer lokal dan _server_. Dapat
dipergunakan perintah Git berikut ini:

    ```shell
    $ git clone https://gitlab.com/voxrow/voxrowlib.git voxrowlib
    ```

2. Masuk ke _folder_ `server/`:

    ```shell
    $ cd voxrowlib/server/
    ```

3. Pastikan GNU Make sudah ada, dengan menjalankan perintah ini:

    ```shell
    $ . make_gnu_install.sh
    ```

    > _Script_ ini hanya dapat dipergunakan di Ubuntu Linux, instalasi untuk OS
    selain ini silahkan cari di internet.

4. Jalankan perintah di komputer lokal dan _server_ sebagai berikut:

    - Komputer lokal:

        ```shell
        $ make local_ssh_key_to_server
        ```

        Ikuti instruksi yang dimintakan saat proses berjalan.

        > Masukkan alamat _server_ dan _username_ `root`.

    - _Server_:

        ```shell
        $ make
        ```

        Ikuti instruksi yang dimintakan saat proses berjalan. Setelah proses berakhir,
        hapuslah _source_code_ VOXROWLib dari _server_, karena sudah tidak diperlukan
        lagi. Perintahnya adalah sebagai berikut:

        ```shell
        $ cd ../../ && rm -rf voxrowlib/
        ```

---

## Lisensi

Lisensi yang dipergunakan adalah [MS-RSL](LICENSE) (Microsoft Reference Source License).
