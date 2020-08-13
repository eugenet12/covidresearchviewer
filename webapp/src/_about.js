import React, { Component } from "react";
import Modal from "react-bootstrap/Modal";

class AboutModal extends Component {
  render() {
    return (
      <Modal
        show={this.props.show}
        onHide={this.props.handleClose}
        id="about-modal"
      >
        <Modal.Header closeButton>
          <Modal.Title>About Covid-19 Research Portal</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <span className="aboutHeader">
            <b>The Big Picture</b>
          </span>
          <br />
          <br />
          <div className="quote text-center">
            <i>
              "The coronavirus pandemic now presents an extra challenge: <br />
              There are far more papers than anyone could ever read."
            </i>
            <br />
            <footer className="blockquote-footer">
              <em>
                <a
                  href="https://www.nytimes.com/article/how-to-read-a-science-study-coronavirus.html"
                  target="_blank"
                >
                  New York Times
                </a>
              </em>
            </footer>
          </div>
          <br />
          <p>
            With the tremendous number of research papers produced each week, it
            is difficult to keep up with the latest developments. We created the
            Covid-19 Research Portal to help medical professionals and
            researchers{" "}
            <b>
              easily find papers of interest by curating and generating
              easy-to-read summaries of the papers
            </b>
            .
          </p>
          <br />
          <span className="aboutHeader">
            <b>Examples</b>
          </span>
          <p>
            <i>See what Covid-19 Research Portal help you discover</i>
          </p>
          <ul>
            <li>
              <a href="/treatment?filters=clinical-trials" target="_blank">
                Find papers on recent clinical trial results
              </a>
            </li>
            <li>
              <a href="/treatment/hydroxychloroquine" target="_blank">
                See the latest on hydroxychloroquine
              </a>
            </li>
            <li>
              <a href="/search/can%20masks%20be%20reused" target="_blank">
                Can face masks be reused?
              </a>
            </li>
          </ul>
          <br />
          <span className="aboutHeader">
            <b>How It Works</b>
          </span>
          <br />
          <span>
            <i>Automated analysis of papers with NLP</i>
          </span>
          <br />
          <br />
          <a href="/model_structure.png" target="_blank">
            <img
              src="/model_structure.png"
              class="img-fluid"
              alt="Model Structure"
            />
          </a>
          <br />
          <br />
          <p>
            Our product is the combination of several NLP models used to
            automatically analyze COVID-19 research papers. Our data is
            downloaded daily from Semantic Scholar (
            <a
              href="https://www.semanticscholar.org/cord19/download"
              target="_blank"
            >
              CORD-19
            </a>
            ), and we also join the papers with data from the{" "}
            <a
              href="https://covid-19tracker.milkeninstitute.org/"
              target="_blank"
            >
              Milken Institute
            </a>{" "}
            to identify papers that discuss drugs of interest and contain
            clinical trial results. After our analysis, all the papers are then
            placed into an{" "}
            <a href="https://www.elastic.co/" target="_blank">
              ElasticSearch
            </a>{" "}
            cluster to enable easy search.
          </p>
          <p>We will be making our code accessible via Github soon.</p>
          <br />
          <span className="aboutHeader">
            <b>Who We Are</b>
          </span>
          <br />
          <p>
            We are a team of data science Master’s students at UC Berkeley
            advised by Joyce Shen and David Steier. Feel free to{" "}
            <a href="mailto:zhou059@gmail.com;eugene.c.tang@gmail.com;czhao@ischool.berkeley.edu;mursil@gmail.com">
              reach out
            </a>{" "}
            if you have any feedback or recommendations on how we can make the
            portal better serve you!
          </p>
          <p className="text-center">
            Mursil Makhani | Eugene Tang | Changjing Zhao | Jonathan Zhou{" "}
          </p>
        </Modal.Body>
      </Modal>
    );
  }
}

export { AboutModal };
