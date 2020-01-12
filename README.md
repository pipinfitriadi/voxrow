# VOXROWLib

Daftar isi:

<!-- TOC -->

- [VOXROWLib](#voxrowlib)
    - [Pengaturan Awal](#pengaturan-awal)
    - [Source-code Editor](#source-code-editor)
        - [Extension](#extension)
    - [Git](#git)
        - [GUI](#gui)
        - [Branching Model](#branching-model)
    - [Lisensi](#lisensi)

<!-- /TOC -->

---

## Pengaturan Awal

1. Pastika sudah terpasang Python dengan minimal versi [3.8.0](https://www.python.org/downloads/release/python-380/).
2. Pastikan _environtment_ lokal sudah terpasang.

    Khusus untuk _distro_ [Debian](https://www.debian.org/) atau [Ubuntu](https://ubuntu.com/),
    terlebih dahulu harus dilakukan instalasi berikut ini:

    ```shell
    $ sudo apt update
    $ sudo apt install python3-pip python3-venv
    ```

    Adapun instruksi untuk memasang _environtment_ lokal adalah sebagai berikut:

    ```shell
    $ python3 -m venv env
    ```

    Instruksi yang terkait _environtment_ lokal yang dapat dipergunakan antara lain:

    - Aktivasi:

        ```shell
        $ . env/bin/activate
        (env) $
        ```

    - Deaktivasi:

        ```shell
        (env) $ deactivate
        $
        ```

3. Pastikan [pustaka pendukung](requirements.txt) terpasang di _environtment_ lokal:

    ```shell
    (env) $ pip install -r requirements.txt
    ```

---

## _Source-code Editor_

[VSCode](https://code.visualstudio.com/) dipergunakan untuk memudahkan dalam
penulisan _source-code_.

### _Extension_

Beberapa _extension_ juga perlu dipasangkan ke VSCode:

- [Auto Markdown TOC](https://marketplace.visualstudio.com/items?itemName=huntertran.auto-markdown-toc)
- [Markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint):
aturan penggunaannya dapat dilihat [di sini](https://github.com/markdownlint/markdownlint/blob/master/docs/RULES.md)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

---

## Git

Dipergunakan [Git](https://git-scm.com/) untuk pengelolaan repositori dari _source
code_.

### GUI

Pada sistem operasi Windows atau MacOS, Git GUI [Sourcetree](https://www.sourcetreeapp.com/)
dapat dipergunakan untuk memudahkan pengelolaan repositori.

### _Branching Model_

Dipergunakan [git-flow](https://github.com/nvie/gitflow) dari Vincent Driessen
untuk memudahkan pengelolaan _feature_, _release_, dan _hotfix_ di dalam
repositori (_branching model_).

---

## Lisensi

Lisensi yang dipergunakan adalah [MS-RSL](LICENSE) (Microsoft Reference Source License).
