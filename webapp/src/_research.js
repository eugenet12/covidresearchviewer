import React, { Component } from "react";

import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Row from "react-bootstrap/Row";
import Tooltip from "react-bootstrap/Tooltip";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faSpinner,
  faUserCheck,
  faNotesMedical,
} from "@fortawesome/free-solid-svg-icons";
import Highcharts from "highcharts";
import HighchartsReact from "highcharts-react-official";
import addHistogramModule from "highcharts/modules/histogram-bellcurve";

addHistogramModule(Highcharts);

import "./_research.css";

String.prototype.capitalize = function () {
  return this.charAt(0).toUpperCase() + this.slice(1);
};

class PaperPublicationGraph extends Component {
  render() {
    const options = {
      chart: {
        height: "100%",
        type: "areaspline",
      },
      title: {
        text: "Number of Publications",
      },
      plotOptions: {
        histogram: {
          accessibility: {
            pointDescriptionFormatter: function (point) {
              let ix = point.index + 1;
              let x1 = point.x.toFixed(3);
              let x2 = point.x2.toFixed(3);
              let val = point.y;
              return ix + ". " + x1 + " to " + x2 + ", " + val + ".";
            },
          },
        },
      },
      series: [
        {
          name: "Count",
          data: this.props.data,
        },
      ],
      xAxis: {
        title: {
          text: "Date",
        },
        type: "datetime",
      },
      yAxis: {
        endOnTick: false,
        title: {
          text: "Number of publications",
        },
      },
      legend: { enabled: false },
      credits: {
        enabled: false,
      },
      annotations: [],
    };
    return (
      <div id="publicationGraphContainer">
        <HighchartsReact highcharts={Highcharts} options={options} />
      </div>
    );
  }
}

class TopTreatments extends Component {
  state = {
    topTreatments: [],
  };
  componentDidMount() {
    fetch("/api/get-top-treatments?size=10")
      .then((res) => res.json())
      .then((res) => {
        this.setState({ topTreatments: res["data"] });
      })
      .catch(console.log);
  }

  renderTopTreatment(treatment) {
    return (
      <li key={treatment["name"] + treatment["num_paper_mentions"]}>
        <a href={"/treatment/" + treatment["name"]}>{treatment["name"]}</a> (
        {treatment["num_paper_mentions"]})
      </li>
    );
  }

  render() {
    let topTreatmentList = this.state.topTreatments.map(
      this.renderTopTreatment
    );
    return (
      <div>
        <span>
          <b>Top-Mentioned Treatments</b>
        </span>
        <ul>{topTreatmentList}</ul>
      </div>
    );
  }
}

class TreatmentDetails extends Component {
  state = {
    treatmentDetails: {
      developer: [], // only pre-include things we have to
      aliases: [],
      next_steps: "",
    },
    showMore: false,
  };

  constructor(props) {
    super(props);
    this.showMore = this.showMore.bind(this);
  }

  componentDidMount() {
    fetch("/api/get-treatment-data?name=" + encodeURIComponent(this.props.name))
      .then((res) => res.json())
      .then((res) => {
        this.setState({ treatmentDetails: res["data"] });
      });
  }

  showMore(e) {
    e.preventDefault();
    this.setState({ showMore: true });
  }

  render() {
    let treatmentDetails;
    let emergencyUseStyle = {};
    if (this.state.treatmentDetails["has_emerg_use_auth"] === "Yes") {
      emergencyUseStyle = { color: "green" };
    }
    if (this.state.showMore) {
      let developers = this.state.treatmentDetails["developer"].join(", ");
      let aliases = this.state.treatmentDetails["aliases"].map((alias) => (
        <li key={alias}>{alias}</li>
      ));
      let nextSteps = this.state.treatmentDetails["next_steps"]
        .split("; ")
        .map((nextStep) => <li key={nextStep}>{nextStep}</li>);
      treatmentDetails = (
        <ul>
          <li>
            <b>Stage:</b> {this.state.treatmentDetails["stage"]}
          </li>
          <li>
            <b>Type:</b> {this.state.treatmentDetails["product_category"]}
          </li>
          <li>
            <b>Description:</b>{" "}
            {this.state.treatmentDetails["product_description"]}
          </li>
          <li>
            <b>Emergency Use Authorization:</b>{" "}
            <span style={emergencyUseStyle}>
              {this.state.treatmentDetails["has_emerg_use_auth"]}
            </span>
          </li>
          <li>
            <b>Research Paper Mentions:</b>{" "}
            {this.state.treatmentDetails["num_paper_mentions"]}
          </li>
          <li>
            <b>Developer:</b> {developers}
          </li>
          <li>
            <b>Next Steps:</b> <ul>{nextSteps}</ul>
          </li>
          <li>
            <b>Aliases:</b> <ul>{aliases}</ul>
          </li>
        </ul>
      );
    } else {
      treatmentDetails = (
        <div>
          <ul>
            <li>
              <b>Stage:</b> {this.state.treatmentDetails["stage"]}
            </li>
            <li>
              <b>Type:</b> {this.state.treatmentDetails["product_category"]}
            </li>
            <li>
              <b>Description:</b>{" "}
              {this.state.treatmentDetails["product_description"]}
            </li>
            <li>
              <b>Emergency Use Authorization:</b>{" "}
              <span style={emergencyUseStyle}>
                {this.state.treatmentDetails["has_emerg_use_auth"]}
              </span>
            </li>
            <li>
              <b>Research Paper Mentions:</b>{" "}
              {this.state.treatmentDetails["num_paper_mentions"]}
            </li>
          </ul>
          <a href="#" onClick={this.showMore}>
            Show More
          </a>
        </div>
      );
    }
    // TODO: add symbol for emergency use authorization
    return (
      <div>
        <span>
          <b>Treatment Details</b>
          {treatmentDetails}
        </span>
      </div>
    );
  }
}

class Paper extends Component {
  state = {
    showFullSummary: false,
    showFullAbstract: false,
  };

  constructor(props) {
    super(props);
    this.toggleshowFullSummary = this.toggleshowFullSummary.bind(this);
    this.toggleShowFullAbstract = this.toggleShowFullAbstract.bind(this);
  }

  toggleshowFullSummary(e) {
    e.preventDefault();
    this.setState({ showFullSummary: !this.state.showFullSummary });
  }

  toggleShowFullAbstract(e) {
    e.preventDefault();
    this.setState({ showFullAbstract: !this.state.showFullAbstract });
  }

  renderPeerReviewTooltop(props) {
    return <Tooltip {...props}>This paper is peer-reviewed</Tooltip>;
  }

  renderClinicalResultTooltop(props) {
    return (
      <Tooltip {...props}>This paper contains a clinical trial result</Tooltip>
    );
  }

  render() {
    let peerReviewed = "";
    if (this.props.paper["is_peer_reviewed"]) {
      peerReviewed = (
        <span>
          {"  "}
          <OverlayTrigger
            placement="top"
            overlay={this.renderPeerReviewTooltop}
          >
            <FontAwesomeIcon icon={faUserCheck} id="peer-review-icon" />
          </OverlayTrigger>
        </span>
      );
    }

    let clinicalResult = "";
    if (this.props.paper["is_clinical_paper"]) {
      clinicalResult = (
        <span>
          {"  "}
          <OverlayTrigger
            placement="top"
            overlay={this.renderClinicalResultTooltop}
          >
            <FontAwesomeIcon icon={faNotesMedical} id="clinical-result-icon" />
          </OverlayTrigger>
        </span>
      );
    }

    let subtitle = (
      <span style={{ marginRight: "0.2rem" }}>
        {this.props.paper["publish_date_for_web"]}
      </span>
    );
    if (this.props.paper["authors"].length > 1) {
      subtitle = (
        <span>
          {subtitle}{" "}
          <span className="verticalLineSmall">
            {" " + this.props.paper["authors"][0] + " et al."}
          </span>
        </span>
      );
    } else if (this.props.paper["authors"].length === 1) {
      subtitle = (
        <span>
          {subtitle}{" "}
          <span className="verticalLineSmall">
            {" " + this.props.paper["authors"][0]}
          </span>
        </span>
      );
    }
    if (
      this.props.paper["journal"].length > 0 &&
      this.props.paper["journal"][0].length > 0
    ) {
      subtitle = (
        <span>
          {subtitle}{" "}
          <span className="verticalLineSmall">
            {" " + this.props.paper["journal"][0]}
          </span>
        </span>
      );
    }
    if (this.props.paper.hasOwnProperty("distance")) {
      subtitle +=
        " | Distance (for debugging): " +
        this.props.paper["distance"].toFixed(3);
    }

    let summary = this.props.paper["scibert_summary_short_cleaned"];
    if (typeof summary === "undefined") {
      summary = "Summary not available.";
    }

    // truncate summary if needed
    let sampleLength = 300;
    let summaryText = (
      <span>
        <em>Machine-Generated Summary</em>: {summary}
      </span>
    );
    if (!this.state.showFullSummary && summary.length > sampleLength) {
      summaryText = (
        <span>
          <em>Machine-Generated Summary</em>:{" "}
          {summary.substring(0, sampleLength) + "... "}
          <a href="#" onClick={this.toggleshowFullSummary}>
            show full summary
          </a>
        </span>
      );
    }

    let abstract = this.props.paper["abstract"];
    let abstractText = (
      <span>
        <a href="#" onClick={this.toggleShowFullAbstract}>
          Show abstract
        </a>
      </span>
    );
    if (typeof abstract === "undefined" || abstract.length === 0) {
      abstractText = (
        <span>
          <em>Abstract not available.</em>
        </span>
      );
    }

    if (this.state.showFullAbstract) {
      abstractText = (
        <span>
          <em>Abstract</em>: {abstract}
        </span>
      );
    }

    let bodyText = (
      <span>
        {summaryText}
        <br />
        <br />
        {abstractText}
      </span>
    );

    if (this.props.paper.hasOwnProperty("sample_sentences")) {
      let sampleSentences = this.props.paper["sample_sentences"];
      let sentenceToDisplay = "";
      if (sampleSentences.hasOwnProperty("abstract")) {
        sentenceToDisplay = sampleSentences["abstract"][0];
      } else if (sampleSentences.hasOwnProperty("text")) {
        sentenceToDisplay = sampleSentences["text"][0];
      }
      if (sentenceToDisplay.length > 0) {
        bodyText = (
          <span>
            <span>
              <em>Snippet</em>:{" "}
              <span dangerouslySetInnerHTML={{ __html: sentenceToDisplay }} />
            </span>
            <br />
            <br />
            {bodyText}
          </span>
        );
      }
    }

    let topics = this.props.paper["topics"].map((topic) => (
      <span className={topic + " topic"} key={topic}>
        {topic}
      </span>
    ));

    let keywords = [];
    if (this.props.paper["top_keywords"].length > 0) {
      keywords = this.props.paper["top_keywords"].slice(0, 5).join(", ");
    }
    return (
      <Card className="w-100 researchPaperContainer">
        <Card.Body>
          <Card.Title>
            <a
              href={this.props.paper["url"][0]}
              target="_blank"
              title={this.props.paper["cord_uid"]}
            >
              {this.props.paper["title"]}
            </a>
            {peerReviewed}
            {clinicalResult}
            <p className="researchPaperSubtitle">{subtitle}</p>
          </Card.Title>
          <Card.Text>{bodyText}</Card.Text>
          Topics: {topics} <span className="verticalLine"></span> Keywords:{" "}
          {keywords}
        </Card.Body>
      </Card>
    );
  }
}

class Filters extends Component {
  constructor(props) {
    super(props);
    this.constructFilter = this.constructFilter.bind(this);
    this.peerReviewedHandleChange = this.peerReviewedHandleChange.bind(this);
    this.clinicalResultsHandleChange = this.clinicalResultsHandleChange.bind(
      this
    );
    this.state = {
      peerReviewedOnly: false,
      clinicalResultsOnly: this.props.filters.includes("clinical-trials"),
    };
  }

  constructFilter() {
    let filter = "";
    if (this.state.peerReviewedOnly) {
      filter += " AND is_peer_reviewed:true";
    }
    if (this.state.clinicalResultsOnly) {
      filter += " AND is_clinical_paper:true";
    }
    this.props.updateFilter(filter);
  }

  peerReviewedHandleChange(e) {
    this.setState({ peerReviewedOnly: e.target.checked }, this.constructFilter);
  }

  clinicalResultsHandleChange(e) {
    this.setState(
      { clinicalResultsOnly: e.target.checked },
      this.constructFilter
    );
  }

  render() {
    let extraFilter = "";
    if (this.props.topic === "treatment") {
      extraFilter = (
        <Form.Check
          type="switch"
          className="form-control-sm"
          id="clinical-results-only-switch"
          label="Clinical Trial Results Only"
          checked={this.state.clinicalResultsOnly}
          onChange={this.clinicalResultsHandleChange}
        />
      );
    }
    return (
      <Form className="form-inline float-right">
        {extraFilter}
        <Form.Check
          type="switch"
          className="form-control-sm"
          id="peer-reviewed-only-switch"
          label="Peer-Reviewed Papers Only"
          checked={this.state.peerReviewedOnly}
          onChange={this.peerReviewedHandleChange}
        />
      </Form>
    );
  }
}

class Research extends Component {
  state = {
    researchPapers: [],
    paperDistribution: [],
    filter: "",
    size: 10,
  };

  constructor(props) {
    super(props);
    this._updateData = this._updateData.bind(this);
    this.renderPaper = this.renderPaper.bind(this);
    this.renderSampleSentence = this.renderSampleSentence.bind(this);
    this.updateData = this.updateData.bind(this);
    this.updateFilter = this.updateFilter.bind(this);
    this.updateSize = this.updateSize.bind(this);
  }

  componentDidMount() {
    this.updateData();
  }

  // get the query given the topic and subtopic
  _updateData(query) {
    fetch(
      "/api/get-recent-topic-research-papers?query=" +
        encodeURIComponent(query) +
        "&filters=" +
        encodeURIComponent(this.state.filter) +
        "&size=" +
        encodeURIComponent(this.state.size)
    )
      .then((res) => res.json())
      .then((res) => {
        this.setState({ researchPapers: res["data"] });
      })
      .catch(console.log);
    fetch(
      "/api/get-recent-paper-distribution?query=" +
        encodeURIComponent(query) +
        "&filters=" +
        encodeURIComponent(this.state.filter)
    )
      .then((res) => res.json())
      .then((res) => {
        this.setState({ paperDistribution: res["data"] });
      })
      .catch(console.log);
  }

  renderSampleSentence(sentence, index) {
    if (index > 5) {
      return "";
    }
    return <li key={index}>{sentence}</li>;
  }

  renderPaper(paper) {
    return <Paper paper={paper} index={0} key={paper["cord_uid"]} />;
  }

  updateData() {
    let query = "topics:" + this.props.topic;
    if (this.props.topic === "latest") {
      query = "*";
    }
    this._updateData(query);
  }

  updateFilter(filter) {
    this.setState({ filter: filter }, this.updateData);
  }

  updateSize() {
    this.setState({ size: this.state.size + 10 }, this.updateData);
  }

  render() {
    let sidebar = <PaperPublicationGraph data={this.state.paperDistribution} />;
    let papers;
    if (this.state.researchPapers.length === 0) {
      papers = <FontAwesomeIcon icon={faSpinner} id="loading-icon" spin />;
    } else {
      papers = this.state.researchPapers.map(this.renderPaper);
    }

    if (this.state.researchPapers.length === this.state.size) {
      papers = (
        <div>
          {papers}
          <div className="w-100 text-center">
            <Button
              variant="link"
              className="showMoreButton"
              onClick={this.updateSize}
            >
              Show More
            </Button>
          </div>
        </div>
      );
    }

    return (
      <Row>
        <Col xs={8}>
          <br />
          <h3 className="contentHeader">{this.props.topic.capitalize()}</h3>
        </Col>
        <Col xs={4} className="text-right">
          <br />
          <Filters
            updateFilter={this.updateFilter}
            topic={this.props.topic}
            filters={this.props.filters}
          />
        </Col>
        <Col xs={3}>{sidebar}</Col>
        <Col xs={9}>{papers}</Col>
      </Row>
    );
  }
}

class SearchResults extends Component {
  state = {
    researchPapers: [],
    paperDistribution: [],
    papersLoaded: false,
    filter: "",
    size: 10,
  };

  constructor(props) {
    super(props);
    this._updateData = this._updateData.bind(this);
    this.renderPaper = this.renderPaper.bind(this);
    this.renderSampleSentence = this.renderSampleSentence.bind(this);
    this.updateData = this.updateData.bind(this);
    this.updateFilter = this.updateFilter.bind(this);
    this.updateSize = this.updateSize.bind(this);
  }

  _updateData(query) {
    fetch(
      "/api/get-paper-search-results?query=" +
        encodeURIComponent(query) +
        "&filters=" +
        encodeURIComponent(this.state.filter) +
        "&size=" +
        encodeURIComponent(this.state.size)
    )
      .then((res) => res.json())
      .then((res) => {
        this.setState({ researchPapers: res["data"], papersLoaded: true });
      })
      .catch(console.log);
    fetch(
      "/api/get-recent-paper-distribution?query=" +
        encodeURIComponent(query) +
        "&filters=" +
        encodeURIComponent(this.state.filter)
    )
      .then((res) => res.json())
      .then((res) => {
        this.setState({ paperDistribution: res["data"] });
      })
      .catch(console.log);
  }

  componentDidMount() {
    this.updateData();
  }

  renderSampleSentence(sentence, index) {
    if (index > 5) {
      return "";
    }
    return <li key={index}>{sentence}</li>;
  }

  renderPaper(paper, i) {
    return (
      <Paper paper={paper} index={i} key={paper["cord_uid"] + i.toString()} />
    );
  }

  updateData() {
    let query = decodeURIComponent(this.props.query);
    this._updateData(query);
  }

  updateFilter(filter) {
    this.setState({ filter: filter }, this.updateData);
  }

  updateSize() {
    this.setState({ size: this.state.size + 10 }, this.updateData);
  }

  render() {
    let papers;
    if (!this.state.papersLoaded) {
      papers = <FontAwesomeIcon icon={faSpinner} id="loading-icon" spin />;
    } else if (this.state.researchPapers.length === 0) {
      papers = <p>No papers found!</p>;
    } else {
      papers = this.state.researchPapers.map(this.renderPaper);
    }

    if (this.state.researchPapers.length === this.state.size) {
      papers = (
        <div>
          {papers}
          <div className="w-100 text-center">
            <Button
              variant="link"
              className="showMoreButton"
              onClick={this.updateSize}
            >
              Show More
            </Button>
          </div>
        </div>
      );
    }

    return (
      <Row>
        <Col xs={8}>
          <br />
          <h3 className="contentHeader">
            Search Results for "<b>{decodeURIComponent(this.props.query)}</b>"
          </h3>
        </Col>
        <Col xs={4} className="text-right">
          <br />
          <Filters
            updateFilter={this.updateFilter}
            topic={this.props.topic}
            filters={this.props.filters}
          />
        </Col>
        <Col sm={3}>
          <PaperPublicationGraph data={this.state.paperDistribution} />
        </Col>
        <Col sm={9}>{papers}</Col>
      </Row>
    );
  }
}

class TreatmentView extends SearchResults {
  constructor(props) {
    super(props);
    this.updateData = this.updateData.bind(this);
    if (this.props.filters.includes("clinical-trials")) {
      this.state["filter"] = " AND is_clinical_paper:true"
    }
  }
  updateData() {
    if (this.props.subtopic.length > 0) {
      fetch(
        "/api/get-treatment-data?name=" +
          encodeURIComponent(this.props.subtopic)
      )
        .then((res) => res.json())
        .then((res) => {
          let subquery = '"' + res["data"]["aliases"].join('" OR "') + '"';
          let query =
            "title:(" +
            subquery +
            ") OR abstract:(" +
            subquery +
            ") OR text:(" +
            subquery +
            ")";
          this._updateData(query);
        })
        .catch(console.log);
    } else {
      this._updateData("topics:treatment");
    }
  }
  render() {
    let title = this.props.topic;
    if (this.props.subtopic.length > 0) {
      title = this.props.topic + ": " + this.props.subtopic;
    }

    let sidebar;
    if (this.props.subtopic.length > 0) {
      sidebar = (
        <div>
          <PaperPublicationGraph data={this.state.paperDistribution} />
          <TreatmentDetails name={this.props.subtopic} />
        </div>
      );
    } else {
      sidebar = (
        <div>
          <PaperPublicationGraph data={this.state.paperDistribution} />
          <TopTreatments />
        </div>
      );
    }

    let papers;
    if (this.state.researchPapers.length === 0) {
      papers = <FontAwesomeIcon icon={faSpinner} id="loading-icon" spin />;
    } else {
      papers = this.state.researchPapers.map(this.renderPaper);
    }

    if (this.state.researchPapers.length === this.state.size) {
      papers = (
        <div>
          {papers}
          <div className="w-100 text-center">
            <Button
              variant="link"
              className="showMoreButton"
              onClick={this.updateSize}
            >
              Show More
            </Button>
          </div>
        </div>
      );
    }

    return (
      <Row>
        <Col xs={8}>
          <br />
          <h3 className="contentHeader">{title.capitalize()}</h3>
        </Col>
        <Col xs={4} className="text-right">
          <br />
          <Filters
            updateFilter={this.updateFilter}
            topic={this.props.topic}
            filters={this.props.filters}
          />
        </Col>
        <Col xs={3}>{sidebar}</Col>
        <Col xs={9}>{papers}</Col>
      </Row>
    );
  }
}

export { Research, SearchResults, TreatmentView };
