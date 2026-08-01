% Bioinformatics class file stub
% This is a minimal placeholder. For submission, download the official
% bioinfo.cls from the OUP Bioinformatics author guidelines:
% https://academic.oup.com/bioinformatics/pages/submission_online
%
% To compile with this stub:
%   pdflatex main.tex
%
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{bioinfo}[2026/07/25 Bioinformatics stub class]

\LoadClass[11pt,twocolumn]{article}

\RequirePackage[margin=2cm]{geometry}
\RequirePackage{natbib}
\RequirePackage{times}

% -- Bioinfo-specific commands (stubs) --
\newcommand{\copyrightyear}[1]{}
\newcommand{\pubyear}[1]{}
\newcommand{\access}[1]{}
\newcommand{\appnotes}[1]{}
\newcommand{\firstpage}[1]{}
\newcommand{\subtitle}[1]{\noindent\textsc{#1}\par\medskip}
\newcommand{\corresp}[1]{\footnotetext{#1}}
\newcommand{\history}[1]{}
\newcommand{\editor}[1]{}
\newcommand{\procemark}{}

\renewenvironment{abstract}{%
  \begin{quote}\small\noindent\textbf{Abstract}\par\medskip
}{%
  \end{quote}
}
